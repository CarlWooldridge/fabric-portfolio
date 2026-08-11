SELECT TOP (1000) [vendorID]
      ,[lpepPickupDatetime]
      ,[lpepDropoffDatetime]
      ,[passengerCount]
      ,[tripDistance]
      ,[puLocationId]
      ,[doLocationId]
      ,[pickupLongitude]
      ,[pickupLatitude]
      ,[dropoffLongitude]
      ,[dropoffLatitude]
      ,[rateCodeID]
      ,[storeAndFwdFlag]
      ,[paymentType]
      ,[fareAmount]
      ,[extra]
      ,[mtaTax]
      ,[improvementSurcharge]
      ,[tipAmount]
      ,[tollsAmount]
      ,[ehailFee]
      ,[totalAmount]
      ,[tripType]


      SELECT FORMAT(COUNT(*),'N0')
      ,MAX(lpepPickupDatetime)
      ,MIN(lpepPickupDatetime)
  FROM [dbo].[taxi_rides_copy_activity]

      SELECT FORMAT(COUNT(*),'N0')
      ,MAX(lpepPickupDatetime)
      ,MIN(lpepPickupDatetime)
  FROM [dbo].[taxi_rides_notebook]


        SELECT FORMAT(COUNT(*),'N0')
      ,MAX(lpepPickupDatetime)
      ,MIN(lpepPickupDatetime)
  FROM [dbo].[taxi_rides_dataflow]


        SELECT FORMAT(COUNT(*),'N0')
      ,MAX(lpepPickupDatetime)
      ,MIN(lpepPickupDatetime)
  FROM [dbo].[taxi_rides_copy_activity_optimize]


SELECT TOP (1000) *
  FROM [dbo].[taxi_rides_copy_activity]



SELECT YEAR(lpepPickupDatetime) AS Yr
,COUNT(*) AS Cnt
    FROM [dbo].[taxi_rides_copy_activity]
GROUP BY YEAR(lpepPickupDatetime)
ORDER BY 1



SELECT * 
FROM [queryinsights].long_running_queries



SELECT * 
FROM [queryinsights].frequently_run_queries


SELECT * 
FROM [queryinsights].active_long_running_queries

SELECT * 
FROM [queryinsights].exec_sessions_history




EXECUTE sys.sp_get_table_health_metrics

EXEC sys.sp_get_table_health_metrics @relation = 'dbo.taxi_rides_copy_activity';



SELECT * FROM dbo.taxi_rides_copy_activity
OPTION (FOR TIMESTAMP AS OF '2026-07-31T14:30:00.000');



SELECT * 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME

SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'taxi_rides_copy_activity'





SELECT 
    column_name,
    [taxi_rides_notebook],
    [taxi_rides_dataflow],
    [taxi_rides_copy_activity]
FROM (
    SELECT 
        TABLE_NAME AS table_name,
        COLUMN_NAME AS column_name,
        DATA_TYPE AS data_type
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
      AND TABLE_NAME IN ('taxi_rides_notebook', 'taxi_rides_dataflow', 'taxi_rides_copy_activity')
) AS src
PIVOT (
    MAX(data_type)
    FOR table_name IN ([taxi_rides_notebook], [taxi_rides_dataflow], [taxi_rides_copy_activity])
) AS pvt
ORDER BY column_name;




SELECT TOP 1000 *
FROM gold.fact_trips



SELECT  TOP 1000
     lpepPickupDatetime AS PickupDatetime
      ,lpepDropoffDatetime AS DropoffDatetime
,DATEDIFF(MINUTE, lpepPickupDatetime,lpepDropoffDatetime)
,DATEDIFF(SECOND, lpepPickupDatetime,lpepDropoffDatetime)
,DATEDIFF(SECOND, lpepPickupDatetime,lpepDropoffDatetime) / 60.0
      ,*
  FROM dbo.taxi_rides_copy_activity_zorder




  SELECT * 
  FROM gold.dim_location_to



  SELECT * 
  FROM gold.dim_location_from
