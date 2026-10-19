with raw as (
    select unnest(packages) as package
    from read_json_auto('{{ env_var("SENTINEL_SNAPSHOT", "fixtures/snapshot.json") }}')
)

select
    package.system as system,
    package.name as name,
    package.version as version,
    package.license as license,
    package.dependent_count as dependent_count
from raw
