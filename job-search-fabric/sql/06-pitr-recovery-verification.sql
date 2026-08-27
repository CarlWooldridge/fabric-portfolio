/* ------------------------------------------------------------------------
   06 — Point-in-time-restore recovery verification
   Run against: JobSearch_DB and JobSearch_DB_backup (Fabric SQL Databases)

   These are the forensics queries from the 2026-08-26 write-back data-loss
   incident. Fact_JobPostings was dropped and recreated while building an
   unrelated feature; the next Dataflow refresh rebuilt it from CSV and, in
   doing so, overwrote the evidence that any write-back had ever existed.
   Recovery used Fabric's automatic point-in-time restore, which creates a
   *new* database (JobSearch_DB_backup) rather than overwriting the original.

   Full post-mortem: ../reference/writeback-incident-postmortem.html

   NOTE ON THE THREE-PART NAMES BELOW — they are deliberate, and they are the
   finding. Cross-database queries fail on Fabric SQL Database's transactional
   endpoint with:

       Msg 40515: Reference to database and/or server name ... is not supported

   They work only on the read-only SQL analytics endpoint, which cannot be an
   UPDATE target. That is an endpoint limitation, not a tooling one: VS Code,
   the Fabric SQL editor and notebooks all fail identically. Moving data
   between two Fabric SQL databases needs a Data pipeline Copy activity or an
   export/import — or, as here, a second connection opened directly against
   the backup database.
   ------------------------------------------------------------------------ */


-- Confirm which database the session is actually connected to before trusting
-- anything below. Cheap, and the mistake it prevents is expensive.
SELECT DB_NAME();


-- How many write-backs survived in the restored copy. This is the number that
-- mattered: 12.
SELECT COUNT(*) AS writeback_rows
FROM   [JobSearch_DB_backup].dbo.Fact_JobPostings
WHERE  WriteBack_Applied = 1;


-- The restored rows in full, for diffing against production.
SELECT Reason, *
FROM   [JobSearch_DB_backup].dbo.Fact_JobPostings
WHERE  WriteBack_Applied = 1;


-- The same population in production, post-incident. Comparing the two sets
-- cell by cell produced the result that made recovery possible: zero differing
-- cells. Production already held the correct values, because the Dataflow had
-- written them back in from the CSV. Only the WriteBack_Applied flag was lost.
--
-- That is worth stating plainly: recovery worked because the CSV happened to
-- mirror every write-back. That is a coincidence of this workflow, not a
-- designed safety net — which is precisely why the write-back store was
-- subsequently split into its own append-only table the Dataflow never writes
-- to.
SELECT Job_ID, Carls_Action, Carls_Action_Date, Outcome, Reason
FROM   dbo.Fact_JobPostings
WHERE  WriteBack_Applied = 1
ORDER BY Job_ID;


-- The repair. Twelve rows, flag only — no data values needed restoring.
-- Left commented, as it was when run, so the affected Job_IDs stay on the
-- record without the statement being executable by accident.
--
-- BEGIN TRANSACTION;
--
-- UPDATE dbo.Fact_JobPostings
-- SET    WriteBack_Applied = 1
-- WHERE  Job_ID IN (4408552442, 4428156532, 4431006891, 4444368338, 4444380121,
--                   4446941237, 4452880525, 4454103847, 4454535147, 4454575250,
--                   4454847118, 4456404565);
--
-- SELECT @@ROWCOUNT AS rows_updated;   -- expect 12
-- COMMIT TRANSACTION;
