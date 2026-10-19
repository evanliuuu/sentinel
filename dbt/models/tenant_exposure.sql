with edges as (
    select
        dependency.system as system,
        dependency.name as name,
        dependency.version as version,
        dependency.depends_on.system as on_system,
        dependency.depends_on.name as on_name,
        dependency.depends_on.version as on_version
    from (
        select unnest(dependencies) as dependency
        from read_json_auto('{{ env_var("SENTINEL_SNAPSHOT", "fixtures/snapshot.json") }}')
    )
)

select
    policy.team as team,
    root.name as root,
    change.system as system,
    change.name as name,
    change.version as version
from read_parquet('{{ env_var("SENTINEL_POLICY_PARQUET", "out/policy.parquet") }}') as policy
inner join read_parquet('{{ env_var("SENTINEL_POLICY_ROOT_PARQUET", "out/policy_root.parquet") }}') as root
    on policy.team = root.team
inner join edges
    on edges.system = root.system
    and edges.name = root.name
    and edges.version = root.version
inner join {{ ref('license_change') }} as change
    on change.system = edges.on_system
    and change.name = edges.on_name
    and change.version = edges.on_version
where lower(change.license) = lower(policy.forbidden_license)
