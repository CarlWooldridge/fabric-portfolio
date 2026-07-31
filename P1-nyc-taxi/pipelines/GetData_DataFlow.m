let
  Source = AzureStorage.Blobs("https://azureopendatastorage.blob.core.windows.net/nyctlc"),
  #"Filtered rows" = Table.SelectRows(Source, each Text.StartsWith([Name], "green/puYear")),
  #"Filtered rows 1" = Table.SelectRows(#"Filtered rows", each ([Extension] = ".parquet")),
  #"Filtered hidden files" = Table.SelectRows(#"Filtered rows 1", each [Attributes]?[Hidden]? <> true),
  #"Added custom" = let
    rootPath = Text.TrimEnd(Value.Metadata(Value.Type(#"Filtered hidden files"))[FileSystemTable.RootPath]?, "/"),
    combinePaths = (path1, path2) => Text.Combine({Text.TrimEnd(path1, "/"), path2}, "/"),
    getRelativePath = (path, relativeTo) => Text.Middle(path, Text.Length(relativeTo) + 1)
in
    Table.AddColumn(#"Filtered hidden files", "Relative Path", each getRelativePath(combinePaths([Folder Path], [Name]), rootPath), type text),
  #"Invoke custom function" = Table.AddColumn(#"Added custom", "Transform file", each #"Transform file"([Content])),
  #"Renamed columns" = Table.RenameColumns(#"Invoke custom function", {{"Relative Path", "Source.Name"}}),
  #"Removed other columns" = Table.SelectColumns(#"Renamed columns", {"Source.Name", "Transform file"}),
  #"Expanded table column" = Table.ExpandTableColumn(#"Removed other columns", "Transform file", Table.ColumnNames(#"Transform file"(#"Sample file"))),
  #"Changed column type" = Table.TransformColumnTypes(#"Expanded table column", {{"vendorID", Int64.Type}, {"lpepPickupDatetime", type datetime}, {"lpepDropoffDatetime", type datetime}, {"passengerCount", Int64.Type}, {"tripDistance", type number}, {"puLocationId", Int64.Type}, {"doLocationId", Int64.Type}, {"rateCodeID", Int64.Type}, {"storeAndFwdFlag", type text}, {"paymentType", Int64.Type}, {"fareAmount", type number}, {"extra", type number}, {"mtaTax", type number}, {"improvementSurcharge", type number}, {"tipAmount", type number}, {"tollsAmount", type number}, {"totalAmount", type number}, {"tripType", Int64.Type}}),
  #"Removed columns" = Table.RemoveColumns(#"Changed column type", {"Source.Name"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"pickupLongitude", type number}, {"pickupLatitude", type number}, {"dropoffLongitude", type number}, {"dropoffLatitude", type number}, {"ehailFee", type number}})
in
  #"Changed column type 1"