/* ------------------------------------------------------------------------
   Fact_Messages — one row per recruiter message thread
   Target: JobSearch_DB (Fabric SQL Database)

   Added late in the project to support triaging inbound recruiter messages
   alongside job postings. Two Fabric findings came out of getting this table
   to exist at all, both documented in the project README:

   1. A Fabric table shortcut maps one *folder* to exactly one Delta table.
      Dropping a second, differently-shaped CSV into the folder an existing
      shortcut already pointed at did not create a second table — it merged the
      new rows into the existing table against the wrong schema, landing them
      as junk with unmatched columns null. The shortcut picker only allows
      selecting folders, never individual files, so there is no UI path to
      disambiguate. The fix is structural: one CSV per folder, one shortcut per
      folder.

   2. Fabric's CSV reader is not multiline-aware. Message and Reply are free
      text and originally contained real embedded newlines — RFC 4180-correct,
      correctly quoted, and parsed fine by Python's csv module — but Fabric
      ends a record at an embedded newline regardless, which shattered 15
      logical rows across 376 physical lines. The upstream writer now flattens
      any run of line breaks to a single ' ¶ ' marker before writing. Restore
      them at the report layer with SUBSTITUTE([Reply], " ¶ ", UNICHAR(10)).

   Message_Date_Only exists because Direct Lake relationships must join on a
   date-typed key, not a datetime — the same grain lesson from the earlier
   NYC Taxi project. Message_Date keeps the time for sorting and display;
   Message_Date_Only is what relates to Dim_Date.
   ------------------------------------------------------------------------ */

CREATE TABLE dbo.Fact_Messages (
    Thread_ID          NVARCHAR(150)  NOT NULL,   -- opaque LinkedIn thread identifier
    Thread_URL         NVARCHAR(1000)     NULL,
    Message_Date       DATETIME2(0)       NULL,   -- full timestamp, for sort/display
    Message_Date_Only  DATE               NULL,   -- date-typed key -> Dim_Date
    Sender             NVARCHAR(200)      NULL,
    Message            NVARCHAR(MAX)      NULL,   -- newlines flattened to ' ¶ '
    Reply              NVARCHAR(MAX)      NULL,   -- newlines flattened to ' ¶ '
    Status             NVARCHAR(50)       NULL,

    CONSTRAINT PK_Fact_Messages PRIMARY KEY (Thread_ID)
);
