DROP TABLE IF EXISTS #TablesToCopy;

SELECT 
    CAST(TABLE_NAME AS VARCHAR(256)) AS TABLE_NAME,
    ROW_NUMBER() OVER (ORDER BY TABLE_NAME) AS rn
INTO #TablesToCopy
FROM NYCTaxiLH.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'gold';

DECLARE @i INT = 1;
DECLARE @max INT = (SELECT MAX(rn) FROM #TablesToCopy);
DECLARE @tbl VARCHAR(256);
DECLARE @sql VARCHAR(MAX);

WHILE @i <= @max
BEGIN
    SELECT @tbl = TABLE_NAME FROM #TablesToCopy WHERE rn = @i;

    SET @sql = 'DROP TABLE IF EXISTS dbo.' + QUOTENAME(@tbl) + ';';
    EXEC sp_executesql @sql;

    SET @sql = 'CREATE TABLE dbo.' + QUOTENAME(@tbl) + ' AS SELECT * FROM NYCTaxiLH.gold.' + QUOTENAME(@tbl) + ';';
    PRINT @sql;
    EXEC sp_executesql @sql;

    SET @i = @i + 1;
END

DROP TABLE #TablesToCopy;