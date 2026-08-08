# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "<lakehouse-id>",
# META       "default_lakehouse_name": "JobSearch_LH",
# META       "default_lakehouse_workspace_id": "<workspace-id>",
# META       "known_lakehouses": [
# META         {
# META           "id": "<lakehouse-id>"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

tables = ["JobPostings"]

results = []
for t in tables:
    details = spark.sql(f"DESCRIBE DETAIL dbo.{t}").collect()[0]
    results.append({
        "table": t,
        "size_gb": round(details["sizeInBytes"] / (1024**3), 2),
        "num_files": details["numFiles"],
        "avg_file_size_mb": round((details["sizeInBytes"] / details["numFiles"]) / (1024**2), 2)
    })

summary_df = spark.createDataFrame(results).select(
    "table", "size_gb", "num_files", "avg_file_size_mb"
)
display(summary_df)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

