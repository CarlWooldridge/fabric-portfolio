



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_copy_activity;



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_dataflow;



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_notebook;




SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_copy_activity
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;

SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_dataflow
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;


SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_notebook
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;



----------------------



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_copy_activity_optimize;



SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_copy_activity_optimize
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;


----------------------



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_copy_activity_vorder;



SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_copy_activity_vorder
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;

----------------------



SELECT 
    COUNT(*) AS row_count,
    AVG(CAST(tripDistance AS FLOAT)) AS avg_distance,
    SUM(CAST(totalAmount AS FLOAT)) AS total_revenue
FROM dbo.taxi_rides_copy_activity_zorder;



SELECT 
    CAST(lpepPickupDatetime AS DATE) AS trip_date,
    COUNT(*) AS trip_count,
    AVG(CAST(fareAmount AS FLOAT)) AS avg_fare
FROM dbo.taxi_rides_copy_activity_zorder
WHERE lpepPickupDatetime >= '2019-06-01' 
  AND lpepPickupDatetime < '2019-07-01'
GROUP BY CAST(lpepPickupDatetime AS DATE)
ORDER BY trip_date;




SELECT * 
FROM dbo.taxi_summary_mlv