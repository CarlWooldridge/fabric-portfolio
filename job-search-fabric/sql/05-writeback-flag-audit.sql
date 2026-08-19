/* ------------------------------------------------------------------------
   05 — Write-back flag audit
   Run against: JobSearch_DB (Fabric SQL Database)

   WriteBack_Applied is the flag that distinguishes a value written from inside
   the report (via the Translytical Task Flow User Data Function) from one that
   arrived with the CSV load. Before it existed, the Dataflow's merge logic
   could not tell the two apart: any non-null value looked like a write-back,
   so once a CSV-sourced value landed in SQL it permanently blocked later CSV
   edits to that row. The flag makes the distinction explicit — CSV wins unless
   a genuine report write-back happened.

   In the current design this column is derived rather than stored: presence of
   a row in Fact_WriteBack *is* the lock. See ../reference/ for why that change
   was made.
   ------------------------------------------------------------------------ */


-- Every row carrying a genuine report write-back.
SELECT Job_ID, Carls_Action, Carls_Action_Date, Outcome, Reason
FROM   dbo.Fact_JobPostings
WHERE  WriteBack_Applied = 1
ORDER BY Job_ID;


-- Same, with the identifying columns, for eyeballing which decisions came from
-- the report rather than the CSV.
SELECT Job_ID, Carls_Action, Carls_Action_Date, Outcome, Reason,
       WriteBack_Applied, Role_Title, Company
FROM   dbo.Fact_JobPostings
WHERE  WriteBack_Applied = 1
ORDER BY Job_ID;


-- Domain check. A BIT column should only ever be 0 or 1, but this also
-- surfaces NULL — which is the state that caused the original ambiguity, since
-- "no flag recorded" and "flag false" are not the same thing.
SELECT DISTINCT WriteBack_Applied
FROM   dbo.Fact_JobPostings;
