/* ------------------------------------------------------------------------
   01 — Table profiling and null checks
   Run against: JobSearch_DB (Fabric SQL Database), transactional endpoint

   First-pass profiling after each Dataflow Gen2 run, to answer "did the load
   actually produce what I think it did" before trusting anything downstream.
   The habit carried over from P1: row counts and null checks, not a green
   "Succeeded" status, are what confirm a load worked.
   ------------------------------------------------------------------------ */


-- Full column surface of the fact table. Worth running once after any schema
-- change: the column list here is the fastest way to confirm that a Dataflow
-- destination mapping actually landed every column it claimed to.
SELECT TOP (1000)
       [Job_ID], [Date_Evaluated], [Company], [Role_Title], [Location],
       [Location_City], [Location_State], [Work_Type], [Employment_Type],
       [Comp_Min], [Comp_Max], [Comp_Mid],
       [Applicant_Volume], [Applicant_Volume_Num],
       [Source], [URL], [Verdict], [Score], [Role_Type], [Comp_Flag],
       [Biggest_Gap], [Biggest_Strength], [Recommended_Action],
       [Carls_Action], [Carls_Action_Date], [Outcome], [Reason], [Notes],
       [ScoreFormula],
       [Pts_Lane], [Pts_Scope], [Pts_Comp], [Pts_Location],
       [Pts_Skills], [Pts_Perks], [Pts_Applicants], [Pts_Deductions],
       [Is_Capped_Score]
FROM   [dbo].[Fact_JobPostings];


-- Null-date checks. Date_Evaluated should never be null (every row is
-- evaluated on some date); Carls_Action_Date legitimately is null for any
-- posting not yet acted on, so this one is a population count, not an error
-- check. Distinguishing the two mattered when building Days_To_Action.
SELECT Carls_Action_Date, *
FROM   [dbo].[Fact_JobPostings]
WHERE  Carls_Action_Date IS NULL;

SELECT Date_Evaluated, *
FROM   [dbo].[Fact_JobPostings]
WHERE  Date_Evaluated IS NULL;


-- Primary key sanity. Job_ID is the write-back target, so a null or empty
-- value here would mean a row the User Data Function could never update.
SELECT *
FROM   [dbo].[Fact_JobPostings]
WHERE  Job_ID IS NULL OR Job_ID = '';


-- Most recent evaluations first — the everyday "what just landed" query.
SELECT *
FROM   [dbo].[Fact_JobPostings]
ORDER BY Date_Evaluated DESC;


-- Type agreement across the relationship. Direct Lake enforces exact type
-- matching on relationship keys with no implicit coercion, so confirming both
-- sides of Job_ID report the same DATA_TYPE is cheaper than debugging a
-- refused relationship in the model later.
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  COLUMN_NAME = 'Job_ID'
  AND  TABLE_NAME IN ('Fact_JobPostings', 'Bridge_ScoreComponents');
