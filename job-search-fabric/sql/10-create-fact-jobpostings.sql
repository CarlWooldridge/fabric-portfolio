/* ------------------------------------------------------------------------
   Fact_JobPostings — the main table, one row per evaluated job posting
   Target: JobSearch_DB (Fabric SQL Database)

   Generated from the live deployed schema (INFORMATION_SCHEMA + sys.indexes),
   not from the original CREATE script — the two had diverged. Columns 39-43
   were added by ALTER over the life of the project and only exist here.

   WHY A FABRIC SQL DATABASE RATHER THAN A LAKEHOUSE TABLE:
   this table is the target of report write-back via a Translytical Task Flow.
   Fabric SQL Database is the only Fabric item type with enforced primary keys
   and reliable row-level UPDATE targeting; Lakehouse and Warehouse SQL
   endpoints don't support that. It still feeds a Direct Lake semantic model,
   because Fabric SQL Database mirrors its tables into OneLake automatically.

   ON COLUMN SIZES: every NVARCHAR length here was measured against the real
   source data, not guessed. Guessing cost two failed refreshes — Work_Type
   was declared NVARCHAR(50) against values running to 150 characters, and
   Days_To_Action_Bucket was declared NVARCHAR(20) against the 25-character
   literal 'Applied before evaluation'. SQL rejects the whole batch with
   "String or binary data would be truncated" rather than silently trimming.
   ------------------------------------------------------------------------ */

CREATE TABLE dbo.Fact_JobPostings (
    -- Identity and source
    Job_ID                   BIGINT         NOT NULL,
    Date_Evaluated           DATE               NULL,
    Company                  NVARCHAR(200)      NULL,
    Role_Title               NVARCHAR(300)      NULL,
    Source                   NVARCHAR(100)      NULL,
    URL                      NVARCHAR(1000)     NULL,

    -- Location, split out of a single free-text field in Dataflow Gen2
    Location                 NVARCHAR(200)      NULL,
    Location_City            NVARCHAR(100)      NULL,
    Location_State           NVARCHAR(100)      NULL,
    Work_Type                NVARCHAR(300)      NULL,   -- needs real headroom
    Employment_Type          NVARCHAR(200)      NULL,

    -- Compensation, parsed from a posted range like "$127,700.00 - $185,150.00"
    Comp_Min                 FLOAT              NULL,
    Comp_Max                 FLOAT              NULL,
    Comp_Mid                 FLOAT              NULL,
    Comp_Flag                NVARCHAR(300)      NULL,

    -- Applicant volume: source is text ("26 applicants", "Over 100 applicants"),
    -- so a numeric twin is parsed upstream to make it plottable.
    Applicant_Volume         NVARCHAR(100)      NULL,
    Applicant_Volume_Num     INT                NULL,

    -- Rubric output
    Verdict                  NVARCHAR(50)       NULL,
    Score                    INT                NULL,
    Score_Raw                INT                NULL,
    Role_Type                NVARCHAR(150)      NULL,
    Biggest_Gap              NVARCHAR(MAX)      NULL,
    Biggest_Strength         NVARCHAR(MAX)      NULL,
    Recommended_Action       NVARCHAR(MAX)      NULL,
    Notes                    NVARCHAR(MAX)      NULL,

    -- Score components, parsed out of the Notes formula clause
    -- ("Score X = Lane 12 + Scope 8 + ..."). Pts_ prefix is deliberate: it
    -- keeps rubric points visually distinct from the dollar Comp_* columns.
    ScoreFormula             NVARCHAR(MAX)      NULL,
    Pts_Lane                 INT                NULL,
    Pts_Scope                INT                NULL,
    Pts_Comp                 INT                NULL,
    Pts_Location             INT                NULL,
    Pts_Skills               INT                NULL,
    Pts_Perks                INT                NULL,
    Pts_Applicants           INT                NULL,
    Pts_Deductions           INT                NULL,   -- NULL on capped rows, deliberately
    Is_Capped_Score          BIT                NULL,

    -- Write-back fields. These exist in the source CSV *and* are writable from
    -- the report, which is what made the merge logic in the dataflow necessary.
    Carls_Action             NVARCHAR(50)       NULL,
    Carls_Action_Date        DATE               NULL,
    Outcome                  NVARCHAR(100)      NULL,   -- append-only log: "Interview; Rejected"
    Reason                   NVARCHAR(500)      NULL,

    -- Derived indicator. Now computed by the dataflow from presence of a row
    -- in Fact_WriteBack rather than stored independently — see 13-.
    WriteBack_Applied        BIT            NOT NULL,

    -- Days-to-action, bucketed upstream because Power BI's own grouping/binning
    -- feature is unavailable over a live connection to a semantic model.
    Days_To_Action           INT                NULL,
    Days_To_Action_Bin_Start INT                NULL,   -- sort key for the bucket
    Days_To_Action_Bucket    NVARCHAR(50)       NULL,

    CONSTRAINT PK_Fact_JobPostings PRIMARY KEY (Job_ID)
);
