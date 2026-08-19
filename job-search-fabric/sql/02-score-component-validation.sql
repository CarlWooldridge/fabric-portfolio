/* ------------------------------------------------------------------------
   02 — Score-component bridge validation
   Run against: JobSearch_DB (Fabric SQL Database)

   The bridge table is produced by unpivoting the eight Pts_* columns out of
   the cleaned fact query in Dataflow Gen2. These queries verify the unpivot
   produced what it should — the check that caught Pts_Deductions being
   missing from the column list entirely, which would have left the waterfall
   chart silently short one category.

   ARCHAEOLOGY: the first two queries still name dbo.Fact_ScoreComponents.
   That was the table's original name, before it was given an explicit
   CREATE TABLE with a composite (Job_ID, Component) primary key and renamed
   Bridge_ScoreComponents — "Fact_" implied a second independent fact table
   when it is really a bridge. Both names appear here because that is how the
   file actually aged; the rename is the correction.
   ------------------------------------------------------------------------ */


-- Component distribution. Eight rows expected, one per Pts_* component.
-- A missing component here means the unpivot column list is incomplete.
SELECT Component, FORMAT(COUNT(*), 'N0') AS Cnt
FROM   dbo.Fact_ScoreComponents          -- pre-rename name; now Bridge_ScoreComponents
GROUP BY Component;


-- Same distribution, but joined back to the fact table. If these counts differ
-- from the ungrouped version above, the bridge contains Job_IDs that no longer
-- exist in the fact table — an orphan check.
SELECT c.Component, FORMAT(COUNT(*), 'N0') AS Cnt
FROM   dbo.Fact_ScoreComponents c        -- pre-rename name; now Bridge_ScoreComponents
JOIN   [dbo].[Fact_JobPostings] p ON p.Job_ID = c.Job_ID
GROUP BY c.Component;


-- Null / blank hunting in the bridge. Points is deliberately null on capped
-- rows for Pts_Deductions only (see 03), so a null here is not automatically a
-- bug — it is a question about which component it belongs to.
-- Each predicate was run on its own; kept as alternatives rather than a single
-- unrunnable stack of WHERE clauses.
SELECT *
FROM   dbo.Bridge_ScoreComponents c
WHERE  (Points IS NULL OR Points = '')
  AND  Points <> 0;
-- WHERE Component IS NULL OR Component = ''
-- WHERE Job_ID   IS NULL OR Job_ID    = ''


-- Full bridge scan, post-rename.
SELECT *
FROM   dbo.Bridge_ScoreComponents c;
