SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [gold].[dim_location_from](
    [LocationId] [int] NULL,
    [Borough] [varchar](8000) NULL,
    [Zone] [varchar](8000) NULL,
    [ServiceZone] [varchar](8000) NULL,
    [NeighborhoodType] [varchar](8000) NULL,
    [IsAirport] [bit] NULL
) ON [PRIMARY]
GO
CREATE CLUSTERED COLUMNSTORE INDEX [ClusteredIndex] ON [gold].[dim_location_from] WITH (DROP_EXISTING = OFF, COMPRESSION_DELAY = 0) ON [PRIMARY]
GO