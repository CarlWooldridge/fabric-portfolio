SELECT vendorID
      ,lpepPickupDatetime AS PickupDatetime
      ,lpepDropoffDatetime AS DropoffDatetime
      ,CAST(lpepPickupDatetime AS date) AS PickupDate
      ,CAST(lpepDropoffDatetime AS date) AS DropoffDate
      ,passengerCount
      ,tripDistance
      ,puLocationId
      ,doLocationId
      ,pickupLongitude
      ,pickupLatitude
      ,dropoffLongitude
      ,dropoffLatitude
      ,rateCodeID
      ,storeAndFwdFlag
      ,paymentType
      ,fareAmount
      ,extra
      ,mtaTax
      ,improvementSurcharge
      ,tipAmount
      ,tollsAmount
      ,ehailFee
      ,totalAmount
      ,tripType
  FROM dbo.taxi_rides_copy_activity_zorder





  EXEC sys.sp_get_table_health_metrics @table_name = 'gold.dim_date';


EXEC sys.sp_get_table_health_metrics @table_name = 'gold.fact_trips';


SELECT [date]
,FORMAT(COUNT(*),'N0') AS Cnt
FROM [external].public_holidays
WHERE countryRegionCode = 'US'
GROUP BY [date]
HAVING COUNT(*) > 1



SELECT TOP 5 * FROM gold.dim_date









SELECT * 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gold'
ORDER BY LOWER(COLUMN_NAME)

SELECT * 
FROM gold.dim_paymenttype




SELECT * 
FROM gold.fact_trips