/* ------------------------------------------------------------------------
   vw_WriteBack_Latest — current write-back state, one row per job
   Target: JobSearch_DB (Fabric SQL Database)

   Reduces the append-only Fact_WriteBack log to its latest row per Job_ID.
   Because each log row is a complete snapshot rather than a delta, "latest row
   wins" is simply correct and the view stays trivial.

   THIS VIEW IS WHAT BREAKS THE CIRCULARITY. The dataflow's Existing_WriteBack
   query points here instead of at Fact_JobPostings, so the dataflow no longer
   reads back from the table it writes. That single redirection is what makes
   Fact_JobPostings safe to drop and rebuild.

   The lock is now presence rather than a stored flag: if a Job_ID appears in
   this view at all, a genuine report write-back happened and its values win
   over the CSV. The dataflow expresses that as

       NormalizeFlag = Table.AddColumn(Expanded, "WriteBack_Applied",
                                       each [WB_Job_ID] <> null, type logical)

   A derived value can't be lost in a DROP the way a stored column can, which
   is precisely the failure this replaced.

   NOTE — this view is deliberately NOT added to the Direct Lake semantic
   model. Direct Lake can only frame real Delta tables mirrored into OneLake; a
   SQL view has no OneLake representation, and adding one to an otherwise
   Direct Lake model falls the *entire model* back to DirectQuery, not just
   that table. The model reads the raw Fact_WriteBack table instead and does
   the latest-row reduction in DAX.
   ------------------------------------------------------------------------ */

CREATE VIEW dbo.vw_WriteBack_Latest AS
SELECT Job_ID, Carls_Action, Carls_Action_Date, Outcome, Reason, Written_At
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY Job_ID ORDER BY WriteBack_ID DESC) AS rn
    FROM dbo.Fact_WriteBack
) t
WHERE rn = 1;
