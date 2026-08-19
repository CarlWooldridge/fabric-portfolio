/* ------------------------------------------------------------------------
   Bridge_ScoreComponents — one row per job per rubric component
   Target: JobSearch_DB (Fabric SQL Database)

   Produced by unpivoting the eight Pts_* columns off the cleaned
   Fact_JobPostings query in Dataflow Gen2. Feeds the Score Component
   Waterfall and the small-multiples-by-Verdict visual.

   NAMED "BRIDGE_", NOT "FACT_": it was originally created as
   Fact_ScoreComponents, which read as a second independent fact table. It
   isn't — it's a bridge from one job to its component scores. The rename came
   with an explicit CREATE TABLE; before that the table had been auto-created
   by the dataflow's "New table" destination option and carried an
   auto-generated MSSQL_System_Uniquifier column, the tell that it had no real
   key.

   GRAIN: (Job_ID, Component) is genuinely unique — a job has at most one value
   per component — so it serves as the primary key with no surrogate needed.

   Points is NOT NULL by design. Pts_Deductions is deliberately NULL on
   capped-score rows, and the dataflow filters those rows out before the write
   rather than storing a meaningless blank component. See 02- for the
   validation queries behind that decision.
   ------------------------------------------------------------------------ */

CREATE TABLE dbo.Bridge_ScoreComponents (
    Job_ID     BIGINT        NOT NULL,
    Component  NVARCHAR(50)  NOT NULL,   -- 'Pts_Lane', 'Pts_Scope', ...
    Points     INT           NOT NULL,

    CONSTRAINT PK_Bridge_ScoreComponents PRIMARY KEY (Job_ID, Component)
);
