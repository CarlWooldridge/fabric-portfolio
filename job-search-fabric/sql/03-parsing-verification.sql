/* ------------------------------------------------------------------------
   03 — Verifying the Dataflow's parsing logic against landed data
   Run against: JobSearch_DB (Fabric SQL Database)

   Direct Lake semantic models support neither Power Query transformations nor
   calculated columns, so every derived field is computed upstream in Dataflow
   Gen2 and lands here as a real column. That makes SQL the only place to check
   whether the parsing actually worked — these queries are the verification
   step for the M code in ../dataflow/mashup.pq.
   ------------------------------------------------------------------------ */


-- Applicant volume parsing. Source values are strings like "26 applicants" or
-- "Over 100 applicants", never bare numbers, so a scatter chart could not plot
-- them until the M layer produced Applicant_Volume_Num ("Over 100" -> 100).
-- Reading the two columns side by side is how the parse was confirmed.
SELECT Applicant_Volume, Applicant_Volume_Num, *
FROM   [dbo].[Fact_JobPostings];


-- Days-to-action bucketing. Power BI's own grouping/binning feature is not
-- available over a live connection to a semantic model, so the histogram's
-- buckets are computed in the Dataflow as a real text column plus a numeric
-- sort key. This confirms which rows actually received a bucket — only rows
-- where both Date_Evaluated and Carls_Action_Date exist.
SELECT *
FROM   [dbo].[Fact_JobPostings]
WHERE  Days_to_Action_Bucket IS NOT NULL;


-- Rows the rubric declined to score. Verdict / Reason / Score_Raw together
-- show whether a "no action" row is genuinely unevaluated or was evaluated and
-- deliberately passed over.
SELECT Verdict, Reason, Score_Raw
FROM   [dbo].[Fact_JobPostings]
WHERE  Carls_Action = 'None';


-- Single-company drill, used while validating a specific posting's parse
-- end to end. Company name replaced with a placeholder for publication.
SELECT p.WriteBack_Applied,
       p.Outcome,
       p.Carls_Action,
       p.Carls_Action_Date,
       p.Reason,
       *
FROM   [dbo].[Fact_JobPostings] p
WHERE  p.Company = '<example-company>';

SELECT p.WriteBack_Applied,
       p.Outcome,
       p.Carls_Action,
       p.Carls_Action_Date,
       p.Reason,
       *
FROM   [dbo].[Fact_JobPostings] p
WHERE  p.Company LIKE '<example-prefix>%';


-- Stable-ordering spot check.
SELECT TOP 100 *
FROM   [dbo].[Fact_JobPostings]
ORDER BY Job_ID;


-- The LinkedIn recruiter-message table, added later than the job log. Its own
-- ingestion story is in the write-up: a Fabric table shortcut maps one folder
-- to exactly one Delta table, so a second CSV dropped beside the first merged
-- into it as junk rather than forming its own table.
SELECT *
FROM   dbo.Fact_Messages;
