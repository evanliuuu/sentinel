import os
import sys
from pathlib import Path

os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


def session():
    from pyspark.sql import SparkSession

    warehouse = Path(os.environ.get("TMPDIR", "/tmp")) / "sentinel-spark"
    warehouse.mkdir(parents=True, exist_ok=True)
    spark = (
        SparkSession.builder.master("local[1]")
        .appName("sentinel")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.warehouse.dir", warehouse.as_posix())
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark
