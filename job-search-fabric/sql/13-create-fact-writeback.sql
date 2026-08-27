/* ------------------------------------------------------------------------
   Fact_WriteBack — append-only log of report-originated write-backs
   Target: JobSearch_DB (Fabric SQL Database)

   *** DO NOT DROP. This table is the only copy of data that exists nowhere ***
   *** else. Unlike every other Fact_* table here, it is NOT produced by the ***
   *** dataflow and cannot be rebuilt from source. The dataflow only READS   ***
   *** it. See ../reference/writeback-incident-postmortem.html.              ***

   WHY THIS TABLE EXISTS
   Write-back values originally lived directly in Fact_JobPostings, and the
   dataflow's Existing_WriteBack query read them back out of that same table to
   preserve them across refreshes. That circularity is what made persistence
   work — and it also meant the table was its own only backup.

   On 2026-08-26 Fact_JobPostings was dropped and recreated while building an
   unrelated feature. The next refresh rebuilt it from CSV and, because an
   empty table is indistinguishable from "no write-back ever happened",
   silently overwrote the evidence that any write-back had existed. No error,
   no warning, and a table that looked completely healthy afterward.

   The fix is this table: write-backs are *source* data, so they belong
   somewhere the dataflow never writes. That makes Fact_JobPostings a genuinely
   disposable derived table — droppable and rebuildable at will, which is what
   it was assumed to be when it was dropped.

   WHY FULL SNAPSHOTS RATHER THAN DELTAS
   Each row records the complete state of all four user-owned fields after that
   write, not just the field that changed. The write-back function does partial
   updates, so an append-only delta log would need per-field "latest non-null"
   resolution to reconstruct current state — genuinely awkward in a view.
   Writing full state makes "latest row wins" correct and keeps the read view
   three lines long (see 14-).

   Written_At / Written_By give an audit trail the previous design had no
   equivalent of: when a decision was made, by whom, and what the state was
   before it.
   ------------------------------------------------------------------------ */

CREATE TABLE dbo.Fact_WriteBack (
    WriteBack_ID       BIGINT IDENTITY(1,1)  NOT NULL,
    Job_ID             BIGINT                NOT NULL,
    Carls_Action       NVARCHAR(50)              NULL,
    Carls_Action_Date  DATE                      NULL,
    Outcome            NVARCHAR(50)              NULL,
    Reason             NVARCHAR(500)             NULL,
    Written_At         DATETIME2(3)          NOT NULL
        CONSTRAINT DF_Fact_WriteBack_Written_At DEFAULT SYSUTCDATETIME(),
    Written_By         NVARCHAR(128)             NULL,

    CONSTRAINT PK_Fact_WriteBack PRIMARY KEY (WriteBack_ID)
);

-- Supports the "latest row per Job_ID" lookup in vw_WriteBack_Latest.
-- DESC on WriteBack_ID so the newest row per job is the leading edge.
CREATE INDEX IX_Fact_WriteBack_Job
    ON dbo.Fact_WriteBack (Job_ID, WriteBack_ID DESC);
