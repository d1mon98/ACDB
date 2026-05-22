using System;

namespace AcDbPlugin.Data
{
    // =========================================================================
    // CLASS A — global catalog models (read-only in this plugin)
    // =========================================================================

    public class EquipCatalog
    {
        public int    EquipCatalogId   { get; set; }
        public string Manufacturer     { get; set; } = "";
        public string Model            { get; set; } = "";
        public string Description      { get; set; } = "";
        public string Type             { get; set; } = "";
        public int?   VoltageRatingV   { get; set; }
        public double? CurrentRatingA  { get; set; }
        public double? IcRatingKa      { get; set; }
        public string InterruptingType { get; set; } = "";
        public string EnclosureNema    { get; set; } = "";
        public double? WeightLbs       { get; set; }
        public string Notes            { get; set; } = "";

        public override string ToString() =>
            $"{Manufacturer} {Model} — {Description} ({Type}, {VoltageRatingV}V)";
    }

    public class CableCatalog
    {
        public int    CableCatalogId    { get; set; }
        public string Manufacturer      { get; set; } = "";
        public string TradeName         { get; set; } = "";
        public string Type              { get; set; } = "";
        public string ConductorMaterial { get; set; } = "";
        public string Insulation        { get; set; } = "";
        public int?   VoltageRatingV    { get; set; }
        public int?   NumConductors     { get; set; }
        public string AwgKcmil          { get; set; } = "";
        public bool   Shield            { get; set; }
        public bool   Armor             { get; set; }
        public double? AmpacityConduitA { get; set; }
        public double? AmpacityTrayA    { get; set; }
        public double? OdInches         { get; set; }
        public double? WeightLbft       { get; set; }
        public string Notes             { get; set; } = "";

        public override string ToString() =>
            $"{Manufacturer} {TradeName} {AwgKcmil} AWG {ConductorMaterial} {Insulation}";
    }

    public class InstrumentCatalog
    {
        public int    InstrumentCatalogId  { get; set; }
        public string Manufacturer         { get; set; } = "";
        public string Model                { get; set; } = "";
        public string Description          { get; set; } = "";
        public string Type                 { get; set; } = "";
        public string SignalType           { get; set; } = "";
        public double? SupplyVdc           { get; set; }
        public string EnclosureNema        { get; set; } = "";
        public string HazardousAreaRating  { get; set; } = "";
        public string Notes                { get; set; } = "";

        public override string ToString() =>
            $"{Manufacturer} {Model} — {Description} ({SignalType})";
    }

    public class ConduitCatalog
    {
        public int    ConduitCatalogId { get; set; }
        public string Type             { get; set; } = "";
        public double? TradeSizeIn     { get; set; }
        public double? OdInches        { get; set; }
        public double? IdInches        { get; set; }
        public string Notes            { get; set; } = "";

        public override string ToString() =>
            $"{Type} {TradeSizeIn}\" trade size";
    }

    // =========================================================================
    // CLASS B — project-specific models
    // =========================================================================

    public class Project
    {
        public int      ProjectId         { get; set; }
        public string   ProjectNumber     { get; set; } = "";
        public string   ProjectName       { get; set; } = "";
        public string   Client            { get; set; } = "";
        public string   Location          { get; set; } = "";
        public string   EngineerOfRecord  { get; set; } = "";
        public DateTime? IssueDate        { get; set; }
        public string   NecEdition        { get; set; } = "";
        public string   VoltageSystem     { get; set; } = "";
        public string   Notes             { get; set; } = "";

        public override string ToString() => $"{ProjectNumber} — {ProjectName}";
    }

    public class Equipment
    {
        public int    EquipId        { get; set; }
        public int    ProjectId      { get; set; }
        public int?   EquipCatalogId { get; set; }
        public string Tag            { get; set; } = "";
        public string Name           { get; set; } = "";
        public int?   BusVoltageV    { get; set; }
        public double? RatedCurrentA { get; set; }
        public double? IcRatingKa   { get; set; }
        public string FedFromTag     { get; set; } = "";
        public double? BreakerTripA  { get; set; }
        public double? BreakerFrameA { get; set; }
        public string DrawingRef     { get; set; } = "";
        public string SheetNumber    { get; set; } = "";
        public string OneLineRef     { get; set; } = "";
        public string Status         { get; set; } = "DESIGN";
        public string Notes          { get; set; } = "";
    }

    public class Instrument
    {
        public int    InstrumentId        { get; set; }
        public int    ProjectId           { get; set; }
        public int?   InstrumentCatalogId { get; set; }
        public string Tag                 { get; set; } = "";
        public string ServiceDescription  { get; set; } = "";
        public string LoopNumber          { get; set; } = "";
        public string PAndIdRef           { get; set; } = "";
        public string PanelTag            { get; set; } = "";
        public string SignalType          { get; set; } = "";
        public string SupplySourceTag     { get; set; } = "";
        public string DrawingRef          { get; set; } = "";
        public string SheetNumber         { get; set; } = "";
        public string Status              { get; set; } = "DESIGN";
        public string Notes               { get; set; } = "";
    }

    public class Cable
    {
        public int    CableId                { get; set; }
        public int    ProjectId              { get; set; }
        public int?   CableCatalogId        { get; set; }
        public string CableTag              { get; set; } = "";
        public string ServiceDescription    { get; set; } = "";
        public int?   FromEquipmentId       { get; set; }
        public int?   FromInstrumentId      { get; set; }
        public string FromTerminal          { get; set; } = "";
        public int?   ToEquipmentId         { get; set; }
        public int?   ToInstrumentId        { get; set; }
        public string ToTerminal            { get; set; } = "";
        public string ConduitTag            { get; set; } = "";
        public string RoutingDescription    { get; set; } = "";
        public double? LengthFt             { get; set; }
        public double? LengthFtActual       { get; set; }
        public int?   NumConductorsUsed     { get; set; }
        public string ConductorSizeAwgKcmil { get; set; } = "";
        public double? VoltageDropPct       { get; set; }
        public string DrawingRef            { get; set; } = "";
        public string SheetNumber           { get; set; } = "";
        public string Status                { get; set; } = "DESIGN";
        public string Notes                 { get; set; } = "";

        // Denormalized display fields — populated by the JOIN query in DbContext
        public string FromTag { get; set; } = "";
        public string ToTag   { get; set; } = "";
    }
}
