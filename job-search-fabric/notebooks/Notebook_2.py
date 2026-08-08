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

import pyspark.sql.functions as F

df = spark.read.table("dbo.JobPostings")

min_dt = df.agg(
    F.min(F.coalesce(F.col("Carls_Action_Date"), F.col("Date_Evaluated")))
).first()[0]

print(min_dt)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

