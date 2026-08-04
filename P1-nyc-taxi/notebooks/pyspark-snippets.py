tables = ["taxi_rides_notebook", "taxi_rides_dataflow", "taxi_rides_copy_activity",
          "taxi_rides_copy_activity_optimize", "taxi_rides_copy_activity_vorder",
          "taxi_rides_copy_activity_zorder"]

results = []
for t in tables:
    details = spark.sql(f"DESCRIBE DETAIL dbo.{t}").collect()[0]
    results.append({
        "table": t,
        "size_gb": round(details["sizeInBytes"] / (1024**3), 2),
        "num_files": details["numFiles"],
        "avg_file_size_mb": round((details["sizeInBytes"] / details["numFiles"]) / (1024**2), 2),
        "clustering_columns": str(details["clusteringColumns"])
    })

summary_df = spark.createDataFrame(results).select(
    "table", "size_gb", "num_files", "avg_file_size_mb", "clustering_columns"
)
display(summary_df)
# All six tables return clustering_columns: [] — Z-Order requested but never
# applied on any variant, since none had enough files/rows left after
# compaction to distribute across. Confirms the finding is structural, not
# specific to one table.