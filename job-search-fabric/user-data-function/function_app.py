from datetime import date
import fabric.functions as fn


udf = fn.UserDataFunctions()

@udf.connection(argName="db", alias="JobSearchDB")
@udf.function()
def update_job_action(
    db: fn.FabricSqlConnection,
    jobId: int,
    carlsAction: str = "",
    outcome: str = "",
    reason: str = "",
    actionDate: str = "",        
) -> str:
    if not carlsAction and not outcome and not reason:
        raise fn.UserThrownError("Provide at least one of Action, Outcome, or Reason to save.")

    conn = db.connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT Carls_Action, Carls_Action_Date, Outcome, Reason
            FROM dbo.vw_WriteBack_Latest WHERE Job_ID = ?
        """, (jobId,))
        prev = cur.fetchone() or (None, None, None, None)

        new_action = carlsAction or prev[0]
        if carlsAction:
            new_date = actionDate or date.today().isoformat()
        else:
            new_date = prev[1]
        new_outcome = outcome or prev[2]
        new_reason  = reason  or prev[3]

        cur.execute("""
            INSERT INTO dbo.Fact_WriteBack
                (Job_ID, Carls_Action, Carls_Action_Date, Outcome, Reason, Written_By)
            VALUES (?, ?, ?, ?, ?, SUSER_SNAME())
        """, (jobId, new_action, new_date, new_outcome, new_reason))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise fn.UserThrownError(f"Write failed: {str(e)}")
