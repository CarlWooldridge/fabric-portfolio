
CREATE PROCEDURE gold.sp_RefreshGoldTables
AS
BEGIN
DROP TABLE IF EXISTS gold.dim_date;
CREATE TABLE gold.dim_date AS SELECT * FROM NYCTaxiLH.gold.dim_date;

DROP TABLE IF EXISTS gold.dim_location_from;
CREATE TABLE gold.dim_location_from AS SELECT * FROM NYCTaxiLH.gold.dim_location_from;

DROP TABLE IF EXISTS gold.dim_location_to;
CREATE TABLE gold.dim_location_to AS SELECT * FROM NYCTaxiLH.gold.dim_location_to;

DROP TABLE IF EXISTS gold.dim_vendor;
CREATE TABLE gold.dim_vendor AS SELECT * FROM NYCTaxiLH.gold.dim_vendor;

DROP TABLE IF EXISTS gold.dim_ratecode;
CREATE TABLE gold.dim_ratecode AS SELECT * FROM NYCTaxiLH.gold.dim_ratecode;

DROP TABLE IF EXISTS gold.dim_paymenttype;
CREATE TABLE gold.dim_paymenttype AS SELECT * FROM NYCTaxiLH.gold.dim_paymenttype;

DROP TABLE IF EXISTS gold.dim_triptype;
CREATE TABLE gold.dim_triptype AS SELECT * FROM NYCTaxiLH.gold.dim_triptype;

DROP TABLE IF EXISTS gold.fact_trips;
CREATE TABLE gold.fact_trips AS SELECT * FROM NYCTaxiLH.gold.fact_trips;

END