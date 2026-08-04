





[lpepPickupDatetime]


SELECT TOP 100 * 
FROM dbo.taxi_rides_copy_activity_zorder;


SELECT DISTINCT vendorID
FROM dbo.taxi_rides_copy_activity_zorder;

SELECT DISTINCT puLocationId AS LocationId
FROM dbo.taxi_rides_copy_activity_zorder
WHERE puLocationId IS NOT NULL
UNION
SELECT DISTINCT doLocationId
FROM dbo.taxi_rides_copy_activity_zorder
WHERE doLocationId IS NOT NULL


SELECT DISTINCT rateCodeID
FROM dbo.taxi_rides_copy_activity_zorder;


SELECT DISTINCT paymentType
FROM dbo.taxi_rides_copy_activity_zorder;


SELECT DISTINCT tripType
FROM dbo.taxi_rides_copy_activity_zorder
WHERe tripType IS NOT NULL

