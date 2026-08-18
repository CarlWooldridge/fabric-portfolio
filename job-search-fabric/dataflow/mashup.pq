[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Fact_JobPostings_DataDestination", IsNewTarget = false], Settings = [Kind = "Manual", AllowCreation = false, ColumnSettings = [Mappings = {[SourceColumnName = "Job_ID", DestinationColumnName = "Job_ID"], [SourceColumnName = "Date_Evaluated", DestinationColumnName = "Date_Evaluated"], [SourceColumnName = "Company", DestinationColumnName = "Company"], [SourceColumnName = "Role_Title", DestinationColumnName = "Role_Title"], [SourceColumnName = "Location", DestinationColumnName = "Location"], [SourceColumnName = "Location_City", DestinationColumnName = "Location_City"], [SourceColumnName = "Location_State", DestinationColumnName = "Location_State"], [SourceColumnName = "Work_Type", DestinationColumnName = "Work_Type"], [SourceColumnName = "Employment_Type", DestinationColumnName = "Employment_Type"], [SourceColumnName = "Comp_Min", DestinationColumnName = "Comp_Min"], [SourceColumnName = "Comp_Max", DestinationColumnName = "Comp_Max"], [SourceColumnName = "Comp_Mid", DestinationColumnName = "Comp_Mid"], [SourceColumnName = "Applicant_Volume", DestinationColumnName = "Applicant_Volume"], [SourceColumnName = "Applicant_Volume_Num", DestinationColumnName = "Applicant_Volume_Num"], [SourceColumnName = "Source", DestinationColumnName = "Source"], [SourceColumnName = "URL", DestinationColumnName = "URL"], [SourceColumnName = "Verdict", DestinationColumnName = "Verdict"], [SourceColumnName = "Score", DestinationColumnName = "Score"], [SourceColumnName = "Role_Type", DestinationColumnName = "Role_Type"], [SourceColumnName = "Comp_Flag", DestinationColumnName = "Comp_Flag"], [SourceColumnName = "Biggest_Gap", DestinationColumnName = "Biggest_Gap"], [SourceColumnName = "Biggest_Strength", DestinationColumnName = "Biggest_Strength"], [SourceColumnName = "Recommended_Action", DestinationColumnName = "Recommended_Action"], [SourceColumnName = "Carls_Action", DestinationColumnName = "Carls_Action"], [SourceColumnName = "Carls_Action_Date", DestinationColumnName = "Carls_Action_Date"], [SourceColumnName = "Outcome", DestinationColumnName = "Outcome"], [SourceColumnName = "Reason", DestinationColumnName = "Reason"], [SourceColumnName = "Notes", DestinationColumnName = "Notes"], [SourceColumnName = "ScoreFormula", DestinationColumnName = "ScoreFormula"], [SourceColumnName = "Pts_Lane", DestinationColumnName = "Pts_Lane"], [SourceColumnName = "Pts_Scope", DestinationColumnName = "Pts_Scope"], [SourceColumnName = "Pts_Comp", DestinationColumnName = "Pts_Comp"], [SourceColumnName = "Pts_Location", DestinationColumnName = "Pts_Location"], [SourceColumnName = "Pts_Skills", DestinationColumnName = "Pts_Skills"], [SourceColumnName = "Pts_Perks", DestinationColumnName = "Pts_Perks"], [SourceColumnName = "Pts_Applicants", DestinationColumnName = "Pts_Applicants"], [SourceColumnName = "Pts_Deductions", DestinationColumnName = "Pts_Deductions"], [SourceColumnName = "Is_Capped_Score", DestinationColumnName = "Is_Capped_Score"], [SourceColumnName = "WriteBack_Applied", DestinationColumnName = "WriteBack_Applied"], [SourceColumnName = "Days_To_Action", DestinationColumnName = "Days_To_Action"], [SourceColumnName = "Days_To_Action_Bin_Start", DestinationColumnName = "Days_To_Action_Bin_Start"], [SourceColumnName = "Days_To_Action_Bucket", DestinationColumnName = "Days_To_Action_Bucket"], [SourceColumnName = "Score_Raw", DestinationColumnName = "Score_Raw"]}], DynamicSchema = false, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Fact_JobPostings = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "<workspace-id>"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "<lakehouse-id>"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "JobPostings", ItemKind = "Table"]}[Data],
       // --- Applicant volume: "26 applicants" / "Over 100 applicants" -> numeric
       CleanApplicants = Table.AddColumn(#"Navigation 2", "Applicant_Volume_Num", each
           let
               raw = [Applicant_Volume],
               isOver100 = raw <> null and Text.Contains(raw, "Over 100"),
               leadingDigits = if raw = null then null else Text.BeforeDelimiter(Text.Trim(raw) & " ", " "),
               parsed = try Number.FromText(leadingDigits) otherwise null
           in
               if raw = null then null
               else if isOver100 then 100
               else parsed
       , type nullable number),

       // --- Comp_Posted split: "$127,700.00 - $185,150.00" -> Comp_Min / Comp_Max / Comp_Mid
       SplitComp = Table.SplitColumn(CleanApplicants, "Comp_Posted",
           Splitter.SplitTextByDelimiter(" - ", QuoteStyle.None),
           {"Comp_Min_Text", "Comp_Max_Text"}),

       CleanNumberFn = (txt as nullable text) as nullable number =>
           let
               cleaned = if txt = null or Text.Trim(txt) = "" then null
                         else Text.Remove(Text.Trim(txt), {"$", ","}),
               result = try Number.FromText(cleaned) otherwise null
           in result,

       AddCompMin = Table.AddColumn(SplitComp, "Comp_Min", each CleanNumberFn([Comp_Min_Text]), type nullable number),
       AddCompMax = Table.AddColumn(AddCompMin, "Comp_Max", each
           let m = CleanNumberFn([Comp_Max_Text]) in if m = null then [Comp_Min] else m
       , type nullable number),
       AddCompMid = Table.AddColumn(AddCompMax, "Comp_Mid", each
           if [Comp_Min] = null then null else ([Comp_Min] + [Comp_Max]) / 2
       , type nullable number),
       RemoveCompHelpers = Table.RemoveColumns(AddCompMid, {"Comp_Min_Text", "Comp_Max_Text"}),

       // --- Location split: "Nashville, TN" / "United States" / "Nashville, TN (multi-city)"
       StripParen = Table.AddColumn(RemoveCompHelpers, "Location_Clean", each
           Text.Trim(Text.BeforeDelimiter([Location], "(")), type text),
       AddCity = Table.AddColumn(StripParen, "Location_City", each
           if Text.Contains([Location_Clean], ",") then Text.Trim(Text.BeforeDelimiter([Location_Clean], ","))
           else null
       , type nullable text),
       AddState = Table.AddColumn(AddCity, "Location_State", each
           if Text.Contains([Location_Clean], ",") then Text.Trim(Text.AfterDelimiter([Location_Clean], ","))
           else Text.Trim([Location_Clean])
       , type nullable text),
       RemoveLocationHelper = Table.RemoveColumns(AddState, {"Location_Clean"}),

       // --- Notes parsing: pull the "Score X = Lane ... + Scope ... " formula clause out,
       // then extract each named component's point value from within it.
       // Prefixed Pts_ rather than Comp_ deliberately, so these rubric-point columns
       // aren't confused with the dollar-value Comp_Min/Comp_Max/Comp_Mid above.
       ExtractFormulaFn = (notes as nullable text) as nullable text =>
           let
               idx = if notes = null then null else Text.PositionOf(notes, "= Lane"),
               after = if idx = null or idx = -1 then null else Text.Range(notes, idx + 2),
               endPos = if after = null then null else Text.PositionOf(after, ". "),
               formula = if after = null then null
                         else if endPos = null or endPos = -1 then after
                         else Text.Range(after, 0, endPos)
           in formula,

       ExtractComponentFn = (formula as nullable text, label as text) as nullable number =>
           let
               searchFor = label & " ",
               hasLabel = formula <> null and Text.Contains(formula, searchFor),
               afterLabel = if hasLabel then Text.AfterDelimiter(formula, searchFor) else null,
               digitsOnly = if afterLabel <> null then Text.BeforeDelimiter(afterLabel & " ", " ") else null,
               numeric = try Number.FromText(digitsOnly) otherwise null
           in if hasLabel then numeric else null,

       AddFormula      = Table.AddColumn(RemoveLocationHelper, "ScoreFormula", each ExtractFormulaFn([Notes]), type nullable text),
       AddLane         = Table.AddColumn(AddFormula,  "Pts_Lane",       each ExtractComponentFn([ScoreFormula], "Lane"),       type nullable number),
       AddScope        = Table.AddColumn(AddLane,     "Pts_Scope",      each ExtractComponentFn([ScoreFormula], "Scope"),      type nullable number),
       AddCompPts      = Table.AddColumn(AddScope,    "Pts_Comp",       each ExtractComponentFn([ScoreFormula], "Comp"),       type nullable number),
       AddLocPts       = Table.AddColumn(AddCompPts,  "Pts_Location",   each ExtractComponentFn([ScoreFormula], "Location"),   type nullable number),
       AddSkills       = Table.AddColumn(AddLocPts,   "Pts_Skills",     each ExtractComponentFn([ScoreFormula], "Skills"),     type nullable number),
       AddPerks        = Table.AddColumn(AddSkills,   "Pts_Perks",      each ExtractComponentFn([ScoreFormula], "Perks"),      type nullable number),
       AddApplicantPts = Table.AddColumn(AddPerks,    "Pts_Applicants", each ExtractComponentFn([ScoreFormula], "Applicants"), type nullable number),

       AddIsCapped = Table.AddColumn(AddApplicantPts, "Is_Capped_Score", each
           [Notes] <> null and Text.Contains([Notes], "capped from")
       , type logical),

       // Deductions computed only for non-capped rows — see the earlier validation
       // against your real data: 26% of rows have "capped from" text whose arithmetic
       // doesn't reconcile against the visible components, so forcing a deduction
       // value there would be misleading rather than informative.
       AddDeductions = Table.AddColumn(AddIsCapped, "Pts_Deductions", each
           let
               namedSum = List.Sum({[Pts_Lane],[Pts_Scope],[Pts_Comp],[Pts_Location],[Pts_Skills],[Pts_Perks],[Pts_Applicants]})
           in
               if [Is_Capped_Score] or namedSum = null or [Score] = null then null
               else [Score] - namedSum
       , type nullable number),
          // --- Preserve write-back values across refreshes ---
          // Carls_Action / Carls_Action_Date / Outcome / Reason exist both as
          // native CSV columns (your existing manual-override fields) and as
          // columns the write-back function updates directly in the SQL table.
          // On every refresh: if the SQL table already has a value, it was set
          // by an earlier CSV load or a report write-back — keep it. Only fall
          // back to the CSV's value when the SQL table has nothing yet. This is
          // what makes a report write-back survive the next Dataflow refresh.

          //made update to work off WriteBack_Applied column
          Merged = Table.NestedJoin(AddDeductions, {"Job_ID"}, Existing_WriteBack, {"Job_ID"}, "WB", JoinKind.LeftOuter),
          Expanded = Table.ExpandTableColumn(Merged, "WB",
              {"Job_ID", "Carls_Action", "Carls_Action_Date", "Outcome", "Reason", "WriteBack_Applied"},
              {"WB_Job_ID", "WB_Carls_Action", "WB_Carls_Action_Date", "WB_Outcome", "WB_Reason", "WB_Applied"}),

          // WB_Applied is null on first run (empty table) or for any Job_ID never touched
          // by a real write-back — treat null the same as false.

           NormalizeFlag = Table.AddColumn(Expanded, "WriteBack_Applied", each [WB_Job_ID] <> null, type logical),


          // Locked = the flag says a genuine report write-back happened for this row.
          // CSV always wins otherwise, regardless of whether SQL currently has a value.
          ResolveText = (csvVal as nullable text, wbVal as nullable text, locked as logical) as nullable text =>
              if locked then wbVal else csvVal,
          ResolveDate = (csvVal as nullable date, wbVal as nullable date, locked as logical) as nullable date =>
              if locked then wbVal else csvVal,

          FinalAction  = Table.AddColumn(NormalizeFlag, "Final_Carls_Action",      each ResolveText([Carls_Action], [WB_Carls_Action], [WriteBack_Applied]), type nullable text),
          FinalDate    = Table.AddColumn(FinalAction,   "Final_Carls_Action_Date", each ResolveDate([Carls_Action_Date], [WB_Carls_Action_Date], [WriteBack_Applied]), type nullable date),
          FinalOutcome = Table.AddColumn(FinalDate,     "Final_Outcome",           each ResolveText([Outcome], [WB_Outcome], [WriteBack_Applied]), type nullable text),
          FinalReason  = Table.AddColumn(FinalOutcome,  "Final_Reason",            each ResolveText([Reason], [WB_Reason], [WriteBack_Applied]), type nullable text),

          RemoveOldWB = Table.RemoveColumns(FinalReason,
              {"Carls_Action", "Carls_Action_Date", "Outcome", "Reason",
               "WB_Carls_Action", "WB_Carls_Action_Date", "WB_Outcome", "WB_Reason", "WB_Applied"}),
          RenameFinal = Table.RenameColumns(RemoveOldWB, {
              {"Final_Carls_Action", "Carls_Action"},
              {"Final_Carls_Action_Date", "Carls_Action_Date"},
              {"Final_Outcome", "Outcome"},
              {"Final_Reason", "Reason"}
          }),
AddDaysToAction = Table.AddColumn(RenameFinal, "Days_To_Action", each
    if [Carls_Action_Date] = null or [Date_Evaluated] = null then null
    else Duration.Days([Carls_Action_Date] - [Date_Evaluated])
, type nullable number),

AddDaysToActionBinStart = Table.AddColumn(AddDaysToAction, "Days_To_Action_Bin_Start", each
    if [Days_To_Action] = null then null
    else if [Days_To_Action] < 0 then -1
    else Number.RoundDown([Days_To_Action] / 5) * 5
, type nullable number),

AddDaysToActionBucket = Table.AddColumn(AddDaysToActionBinStart, "Days_To_Action_Bucket", each
    if [Days_To_Action_Bin_Start] = null then null
    else if [Days_To_Action_Bin_Start] = -1 then "Applied before evaluation"
    else Text.From([Days_To_Action_Bin_Start]) & "-" & Text.From([Days_To_Action_Bin_Start] + 4) & " days"
, type nullable text),
SetWholeNumberTypes = Table.TransformColumnTypes(AddDaysToActionBucket, {
    {"Pts_Lane", Int64.Type}, {"Pts_Scope", Int64.Type}, {"Pts_Comp", Int64.Type},
    {"Pts_Location", Int64.Type}, {"Pts_Skills", Int64.Type}, {"Pts_Perks", Int64.Type},
    {"Pts_Applicants", Int64.Type}, {"Pts_Deductions", Int64.Type},
    {"Applicant_Volume_Num", Int64.Type}, {"Days_To_Action", Int64.Type}, {"Days_To_Action_Bin_Start", Int64.Type}, {"Score_Raw", Int64.Type}
})
      in
          SetWholeNumberTypes;
shared Existing_WriteBack = let
  Source = FabricSql.Contents([HierarchicalNavigation = null]),
  #"Navigation 1" = Source{[workspaceId = "<workspace-id>"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[sqlId = "<sql-database-id>"]}[Data],
#"Navigation 3" = #"Navigation 2"{[Schema = "dbo", Item = "vw_WriteBack_Latest"]}[Data],
#"Removed other columns" = Table.SelectColumns(#"Navigation 3",
    {"Job_ID", "Carls_Action", "Carls_Action_Date", "Outcome", "Reason"})
in
  #"Removed other columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Bridge_ScoreComponents_DataDestination", IsNewTarget = false], Settings = [Kind = "Manual", AllowCreation = false, ColumnSettings = [Mappings = {[SourceColumnName = "Job_ID", DestinationColumnName = "Job_ID"], [SourceColumnName = "Component", DestinationColumnName = "Component"], [SourceColumnName = "Points", DestinationColumnName = "Points"]}], DynamicSchema = false, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Bridge_ScoreComponents = let
  Source = Fact_JobPostings,
  #"Unpivoted only selected columns" = Table.Unpivot(Source, {"Pts_Lane", "Pts_Scope", "Pts_Comp", "Pts_Location", "Pts_Skills", "Pts_Perks", "Pts_Applicants", "Pts_Deductions"}, "Component", "Points"),
  #"Removed columns" = Table.RemoveColumns(#"Unpivoted only selected columns", {"Date_Evaluated", "Company", "Role_Title", "Location", "Work_Type", "Employment_Type", "Applicant_Volume", "Source", "URL", "Verdict", "Score", "Role_Type", "Comp_Flag", "Biggest_Gap", "Biggest_Strength", "Recommended_Action", "Notes", "__filepath__", "__corrupt__", "__ingestion_timestamp__", "Applicant_Volume_Num", "Comp_Min", "Comp_Max", "Comp_Mid", "Location_City", "Location_State", "ScoreFormula", "Is_Capped_Score", "Carls_Action", "Carls_Action_Date", "Outcome", "Reason"}),
  #"Filtered rows" = Table.SelectRows(#"Removed columns", each [Points] <> null and [Points] <> "")
in
  #"Filtered rows";
shared Bridge_ScoreComponents_DataDestination = let
  Pattern = FabricSql.Contents([CreateNavigationProperties = false, HierarchicalNavigation = true]),
  Navigation_1 = Pattern{[workspaceId = "<workspace-id>"]}[Data],
  Navigation_2 = Navigation_1{[sqlId = "<sql-database-id>"]}[Data],
  Navigation_3 = Navigation_2{[Schema = "dbo"]}[Data],
  TableNavigation = Navigation_3{[Name = "Bridge_ScoreComponents"]}[Data]
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Fact_Messages_DataDestination", IsNewTarget = false], Settings = [Kind = "Manual", AllowCreation = false, ColumnSettings = [Mappings = {[SourceColumnName = "Thread_ID", DestinationColumnName = "Thread_ID"], [SourceColumnName = "Thread_URL", DestinationColumnName = "Thread_URL"], [SourceColumnName = "Date", DestinationColumnName = "Message_Date"], [SourceColumnName = "Message_Date_Only", DestinationColumnName = "Message_Date_Only"], [SourceColumnName = "Sender", DestinationColumnName = "Sender"], [SourceColumnName = "Message", DestinationColumnName = "Message"], [SourceColumnName = "Reply", DestinationColumnName = "Reply"], [SourceColumnName = "Status", DestinationColumnName = "Status"]}], DynamicSchema = false, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Fact_Messages = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "<workspace-id>"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "<lakehouse-id>"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "Messages", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 2", {{"Date", type datetime}}),
  #"Duplicated column" = Table.DuplicateColumn(#"Changed column type", "Date", "Message_Date_Only"),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Duplicated column", {{"Message_Date_Only", type date}})
in
  #"Changed column type 1";
shared Fact_Messages_DataDestination = let
  Pattern = FabricSql.Contents([CreateNavigationProperties = false, HierarchicalNavigation = true]),
  Navigation_1 = Pattern{[workspaceId = "<workspace-id>"]}[Data],
  Navigation_2 = Navigation_1{[sqlId = "<sql-database-id>"]}[Data],
  Navigation_3 = Navigation_2{[Schema = "dbo"]}[Data],
  TableNavigation = Navigation_3{[Name = "Fact_Messages"]}[Data]
in
  TableNavigation;
shared Fact_JobPostings_DataDestination = let
  Pattern = FabricSql.Contents([CreateNavigationProperties = false, HierarchicalNavigation = true]),
  Navigation_1 = Pattern{[workspaceId = "<workspace-id>"]}[Data],
  Navigation_2 = Navigation_1{[sqlId = "<sql-database-id>"]}[Data],
  Navigation_3 = Navigation_2{[Schema = "dbo"]}[Data],
  TableNavigation = Navigation_3{[Name = "Fact_JobPostings"]}[Data]
in
  TableNavigation;

