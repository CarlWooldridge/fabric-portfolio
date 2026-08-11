DECLARE @RC int

-- TODO: Set parameter values here.

EXECUTE @RC = [gold].[sp_RefreshGoldTables] 
GO


EXEC sys.sp_get_table_health_metrics @table_name = 'gold.fact_trips';