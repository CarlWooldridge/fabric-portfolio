/* ------------------------------------------------------------------------
   04 — Action and outcome distributions
   Run against: JobSearch_DB (Fabric SQL Database)

   These are the queries behind the report's KPI definitions. Running the
   distributions in SQL first is what exposed that "Carls_Action IS NOT NULL"
   is a much broader population than "actually applied" — 'None', 'Pass' and
   'Skip' are all non-blank strings representing decisions *not* to pursue.
   That distinction changed how Active Applications was defined in DAX.
   ------------------------------------------------------------------------ */


-- The full action distribution. The reason the report's "Active Applications"
-- measure cannot simply test Carls_Action <> BLANK().
SELECT Carls_Action, FORMAT(COUNT(*), 'N0') AS Cnt
FROM   [dbo].[Fact_JobPostings]
GROUP BY Carls_Action;


-- Outcome distribution. Outcome is an append-only status log written by the
-- User Data Function ("Interview; Rejected"), not a single value, so counts
-- here are per distinct chain rather than per stage.
SELECT Outcome, FORMAT(COUNT(*), 'N0') AS Cnt
FROM   [dbo].[Fact_JobPostings]
GROUP BY Outcome;


-- Action x Verdict crosstab. Where the rubric's verdict and the decision
-- actually taken disagree is the interesting cell — a 'Pursue' verdict with a
-- 'Pass' action is either a rubric miss or a judgment call worth recording.
SELECT Carls_Action, Verdict, FORMAT(COUNT(*), 'N0') AS Cnt
FROM   [dbo].[Fact_JobPostings]
GROUP BY Carls_Action, Verdict;


-- Rows in the terminal / declined states.
SELECT Carls_Action, *
FROM   [dbo].[Fact_JobPostings]
WHERE  Carls_Action IN ('Skip', 'Referral', 'Rejected');
