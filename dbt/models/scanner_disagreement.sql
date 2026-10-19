select
    system,
    name,
    version,
    source,
    label,
    note
from read_parquet('{{ env_var("SENTINEL_SCAN_PARQUET", "out/scanner_disagreement.parquet") }}')
