

/*
SELECT 
    start_time,
    end_time,
    total_elapsed_time_ms,
    command
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'
ORDER BY start_time DESC;


SELECT 
    start_time,
    end_time,
    total_elapsed_time_ms,
    command
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'
ORDER BY start_time DESC;


SELECT 
    start_time,
    end_time,
    total_elapsed_time_ms,
    command
FROM queryinsights.exec_requests_history
WHERE command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'
ORDER BY start_time DESC;

*/


SELECT 'taxi_rides_copy_activity' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms) AS avg_elapsed_time_ms
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_copy_activity%'
AND command NOT LIKE '%queryinsights%'
AND command NOT LIKE '%optimize%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_dataflow' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_dataflow%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_notebook' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_notebook%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'


UNION ALL



SELECT 'taxi_rides_copy_activity' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_copy_activity%'
AND command NOT LIKE '%queryinsights%'
AND command NOT LIKE '%optimize%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_dataflow' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_dataflow%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_notebook' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_notebook%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'


UNION ALL

SELECT 'taxi_rides_copy_activity_optimize' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_copy_activity_optimize%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_copy_activity_optimize' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_copy_activity_optimize%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_copy_activity_vorder' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_copy_activity_vorder%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_copy_activity_vorder' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_copy_activity_vorder%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_copy_activity_zorder' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_distance%taxi_rides_copy_activity_zorder%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'

UNION ALL

SELECT 'taxi_rides_copy_activity_zorder' AS tbl, 'query2' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%avg_fare%taxi_rides_copy_activity_zorder%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'


UNION ALL

SELECT 'taxi_summary_mlv' AS tbl, 'query1' AS qry,
    AVG(total_elapsed_time_ms)
    ,COUNT(*) AS Runs
FROM queryinsights.exec_requests_history
WHERE command LIKE '%FROM dbo.taxi_summary_mlv%'
AND command NOT LIKE '%queryinsights%'
AND start_time >= '2026-08-02'


ORDER BY 3, 2, 1





