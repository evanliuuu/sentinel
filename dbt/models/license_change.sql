select
    change.system,
    change.name,
    change.version,
    change.previous_license,
    change.license,
    version.dependent_count
from read_parquet('{{ env_var("SENTINEL_LICENSE_PARQUET", "out/license_change.parquet") }}') as change
inner join {{ ref('package_version') }} as version
    on change.system = version.system
    and change.name = version.name
    and change.version = version.version
