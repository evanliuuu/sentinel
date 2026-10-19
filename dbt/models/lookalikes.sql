select
    system,
    name,
    version,
    popular_name,
    edit_distance,
    score
from read_parquet('{{ env_var("SENTINEL_LOOKALIKE_PARQUET", "out/lookalikes.parquet") }}')
