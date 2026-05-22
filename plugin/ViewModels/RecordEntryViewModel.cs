using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using AcDbPlugin.Data;

namespace AcDbPlugin.ViewModels
{
    public enum RecordType { Equipment, Instrument, Cable }

    /// <summary>
    /// Shared ViewModel for the Add / Edit modal window.
    /// Visibility flags drive which field section is shown in the XAML.
    /// </summary>
    public class RecordEntryViewModel : ViewModelBase
    {
        private readonly DbContext _db;
        private readonly int _projectId;

        public RecordEntryViewModel(RecordType type, DbContext db, int projectId)
        {
            RecordType = type;
            _db        = db;
            _projectId = projectId;

            IsEquipment  = type == RecordType.Equipment;
            IsInstrument = type == RecordType.Instrument;
            IsCable      = type == RecordType.Cable;

            Title = type switch
            {
                RecordType.Equipment  => "Equipment Record",
                RecordType.Instrument => "Instrument Record",
                RecordType.Cable      => "Cable Record",
                _                     => "Record",
            };
        }

        public RecordType RecordType { get; }

        // Title / section visibility
        public string Title        { get; }
        public bool   IsEquipment  { get; }
        public bool   IsInstrument { get; }
        public bool   IsCable      { get; }

        // Catalog pickers
        public ObservableCollection<EquipCatalog>      EquipCatalogs      { get; } = new();
        public ObservableCollection<InstrumentCatalog> InstrumentCatalogs { get; } = new();
        public ObservableCollection<CableCatalog>      CableCatalogs      { get; } = new();

        private EquipCatalog?      _selectedEquipCat;
        private InstrumentCatalog? _selectedInstrCat;
        private CableCatalog?      _selectedCableCat;

        public EquipCatalog? SelectedEquipCatalog
        {
            get => _selectedEquipCat;
            set { if (Set(ref _selectedEquipCat, value)) ApplyEquipCatalog(value); }
        }

        public InstrumentCatalog? SelectedInstrumentCatalog
        {
            get => _selectedInstrCat;
            set { if (Set(ref _selectedInstrCat, value)) ApplyInstrCatalog(value); }
        }

        public CableCatalog? SelectedCableCatalog
        {
            get => _selectedCableCat;
            set { if (Set(ref _selectedCableCat, value)) ApplyCableCatalog(value); }
        }

        // ------------------------------------------------------------------ //
        // Shared fields
        // ------------------------------------------------------------------ //
        private string _tag = "";
        public string Tag { get => _tag; set => Set(ref _tag, value?.ToUpperInvariant() ?? ""); }

        private string _status = "DESIGN";
        public string Status { get => _status; set => Set(ref _status, value); }

        private string _drawingRef = "";
        public string DrawingRef { get => _drawingRef; set => Set(ref _drawingRef, value); }

        private string _sheetNumber = "";
        public string SheetNumber { get => _sheetNumber; set => Set(ref _sheetNumber, value); }

        private string _notes = "";
        public string Notes { get => _notes; set => Set(ref _notes, value); }

        public System.Collections.Generic.List<string> StatusOptions { get; } =
            new System.Collections.Generic.List<string>
            { "DESIGN", "ISSUED", "PURCHASED", "INSTALLED", "COMMISSIONED" };

        // ------------------------------------------------------------------ //
        // Equipment fields
        // ------------------------------------------------------------------ //
        private string _name = "";
        public string Name { get => _name; set => Set(ref _name, value); }

        private string _busVoltageV = "";
        public string BusVoltageV { get => _busVoltageV; set => Set(ref _busVoltageV, value); }

        private string _fedFromTag = "";
        public string FedFromTag { get => _fedFromTag; set => Set(ref _fedFromTag, value?.ToUpperInvariant() ?? ""); }

        private string _breakerTripA = "";
        public string BreakerTripA { get => _breakerTripA; set => Set(ref _breakerTripA, value); }

        private string _breakerFrameA = "";
        public string BreakerFrameA { get => _breakerFrameA; set => Set(ref _breakerFrameA, value); }

        private string _oneLineRef = "";
        public string OneLineRef { get => _oneLineRef; set => Set(ref _oneLineRef, value); }

        // ------------------------------------------------------------------ //
        // Instrument fields
        // ------------------------------------------------------------------ //
        private string _serviceDescription = "";
        public string ServiceDescription { get => _serviceDescription; set => Set(ref _serviceDescription, value); }

        private string _loopNumber = "";
        public string LoopNumber { get => _loopNumber; set => Set(ref _loopNumber, value); }

        private string _pAndIdRef = "";
        public string PAndIdRef { get => _pAndIdRef; set => Set(ref _pAndIdRef, value); }

        private string _panelTag = "";
        public string PanelTag { get => _panelTag; set => Set(ref _panelTag, value?.ToUpperInvariant() ?? ""); }

        private string _signalType = "";
        public string SignalType { get => _signalType; set => Set(ref _signalType, value); }

        private string _supplySourceTag = "";
        public string SupplySourceTag { get => _supplySourceTag; set => Set(ref _supplySourceTag, value?.ToUpperInvariant() ?? ""); }

        // ------------------------------------------------------------------ //
        // Cable fields
        // ------------------------------------------------------------------ //
        private string _cableTag = "";
        public string CableTag { get => _cableTag; set => Set(ref _cableTag, value?.ToUpperInvariant() ?? ""); }

        private string _fromTag = "";
        public string FromTag { get => _fromTag; set => Set(ref _fromTag, value?.ToUpperInvariant() ?? ""); }

        private string _fromTerminal = "";
        public string FromTerminal { get => _fromTerminal; set => Set(ref _fromTerminal, value); }

        private string _toTag = "";
        public string ToTag { get => _toTag; set => Set(ref _toTag, value?.ToUpperInvariant() ?? ""); }

        private string _toTerminal = "";
        public string ToTerminal { get => _toTerminal; set => Set(ref _toTerminal, value); }

        private string _conduitTag = "";
        public string ConduitTag { get => _conduitTag; set => Set(ref _conduitTag, value?.ToUpperInvariant() ?? ""); }

        private string _lengthFt = "";
        public string LengthFt { get => _lengthFt; set => Set(ref _lengthFt, value); }

        private string _conductorSize = "";
        public string ConductorSize { get => _conductorSize; set => Set(ref _conductorSize, value); }

        // ------------------------------------------------------------------ //
        // Load existing records (Edit mode)
        // ------------------------------------------------------------------ //

        public void LoadEquipment(Equipment e)
        {
            Tag           = e.Tag;
            Name          = e.Name;
            BusVoltageV   = e.BusVoltageV?.ToString() ?? "";
            FedFromTag    = e.FedFromTag;
            BreakerTripA  = e.BreakerTripA?.ToString() ?? "";
            BreakerFrameA = e.BreakerFrameA?.ToString() ?? "";
            OneLineRef    = e.OneLineRef;
            DrawingRef    = e.DrawingRef;
            SheetNumber   = e.SheetNumber;
            Status        = e.Status;
            Notes         = e.Notes;

            if (e.EquipCatalogId.HasValue)
                foreach (var c in EquipCatalogs)
                    if (c.EquipCatalogId == e.EquipCatalogId.Value)
                    { _selectedEquipCat = c; OnPropertyChanged(nameof(SelectedEquipCatalog)); break; }
        }

        public void LoadInstrument(Instrument i)
        {
            Tag               = i.Tag;
            ServiceDescription = i.ServiceDescription;
            LoopNumber        = i.LoopNumber;
            PAndIdRef         = i.PAndIdRef;
            PanelTag          = i.PanelTag;
            SignalType        = i.SignalType;
            SupplySourceTag   = i.SupplySourceTag;
            DrawingRef        = i.DrawingRef;
            SheetNumber       = i.SheetNumber;
            Status            = i.Status;
            Notes             = i.Notes;

            if (i.InstrumentCatalogId.HasValue)
                foreach (var c in InstrumentCatalogs)
                    if (c.InstrumentCatalogId == i.InstrumentCatalogId.Value)
                    { _selectedInstrCat = c; OnPropertyChanged(nameof(SelectedInstrumentCatalog)); break; }
        }

        public void LoadCable(Cable c)
        {
            CableTag          = c.CableTag;
            ServiceDescription = c.ServiceDescription;
            FromTag           = c.FromTag;
            FromTerminal      = c.FromTerminal;
            ToTag             = c.ToTag;
            ToTerminal        = c.ToTerminal;
            ConduitTag        = c.ConduitTag;
            LengthFt          = c.LengthFt?.ToString() ?? "";
            ConductorSize     = c.ConductorSizeAwgKcmil;
            DrawingRef        = c.DrawingRef;
            SheetNumber       = c.SheetNumber;
            Status            = c.Status;
            Notes             = c.Notes;

            if (c.CableCatalogId.HasValue)
                foreach (var cat in CableCatalogs)
                    if (cat.CableCatalogId == c.CableCatalogId.Value)
                    { _selectedCableCat = cat; OnPropertyChanged(nameof(SelectedCableCatalog)); break; }
        }

        // ------------------------------------------------------------------ //
        // Convert back to model objects
        // ------------------------------------------------------------------ //

        public Equipment ToEquipment() => new Equipment
        {
            ProjectId      = _projectId,
            EquipCatalogId = _selectedEquipCat?.EquipCatalogId,
            Tag            = Tag.ToUpperInvariant(),
            Name           = Name,
            BusVoltageV    = int.TryParse(BusVoltageV, out var bv) ? bv : (int?)null,
            FedFromTag     = FedFromTag,
            BreakerTripA   = double.TryParse(BreakerTripA, out var bt) ? bt : (double?)null,
            BreakerFrameA  = double.TryParse(BreakerFrameA, out var bf) ? bf : (double?)null,
            OneLineRef     = OneLineRef,
            DrawingRef     = DrawingRef,
            SheetNumber    = SheetNumber,
            Status         = Status,
            Notes          = Notes,
        };

        public Instrument ToInstrument() => new Instrument
        {
            ProjectId           = _projectId,
            InstrumentCatalogId = _selectedInstrCat?.InstrumentCatalogId,
            Tag                 = Tag.ToUpperInvariant(),
            ServiceDescription  = ServiceDescription,
            LoopNumber          = LoopNumber,
            PAndIdRef           = PAndIdRef,
            PanelTag            = PanelTag,
            SignalType          = SignalType,
            SupplySourceTag     = SupplySourceTag,
            DrawingRef          = DrawingRef,
            SheetNumber         = SheetNumber,
            Status              = Status,
            Notes               = Notes,
        };

        public Cable ToCable() => new Cable
        {
            ProjectId              = _projectId,
            CableCatalogId         = _selectedCableCat?.CableCatalogId,
            CableTag               = CableTag.ToUpperInvariant(),
            ServiceDescription     = ServiceDescription,
            // FROM/TO resolved by tag lookup in Integration or CLI — stored as denormalized here
            FromTerminal           = FromTerminal,
            ToTerminal             = ToTerminal,
            ConduitTag             = ConduitTag,
            LengthFt               = double.TryParse(LengthFt, out var lft) ? lft : (double?)null,
            ConductorSizeAwgKcmil  = ConductorSize,
            DrawingRef             = DrawingRef,
            SheetNumber            = SheetNumber,
            Status                 = Status,
            Notes                  = Notes,
            // FromTag/ToTag are display-only; FK resolution is done in CLI/Python side
            FromTag                = FromTag,
            ToTag                  = ToTag,
        };

        // ------------------------------------------------------------------ //
        // Catalog load & apply
        // ------------------------------------------------------------------ //

        public async Task LoadCatalogsAsync()
        {
            try
            {
                if (IsEquipment)
                {
                    var cats = await _db.GetEquipCatalogAsync();
                    EquipCatalogs.Clear();
                    foreach (var c in cats) EquipCatalogs.Add(c);
                }
                else if (IsInstrument)
                {
                    var cats = await _db.GetInstrumentCatalogAsync();
                    InstrumentCatalogs.Clear();
                    foreach (var c in cats) InstrumentCatalogs.Add(c);
                }
                else if (IsCable)
                {
                    var cats = await _db.GetCableCatalogAsync();
                    CableCatalogs.Clear();
                    foreach (var c in cats) CableCatalogs.Add(c);
                }
            }
            catch { /* non-fatal — catalogs may be empty */ }
        }

        private void ApplyEquipCatalog(EquipCatalog? c)
        {
            if (c == null) return;
            if (string.IsNullOrEmpty(Name)) Name = c.Description;
            if (string.IsNullOrEmpty(BusVoltageV)) BusVoltageV = c.VoltageRatingV?.ToString() ?? "";
        }

        private void ApplyInstrCatalog(InstrumentCatalog? c)
        {
            if (c == null) return;
            if (string.IsNullOrEmpty(SignalType)) SignalType = c.SignalType;
        }

        private void ApplyCableCatalog(CableCatalog? c)
        {
            if (c == null) return;
            if (string.IsNullOrEmpty(ConductorSize)) ConductorSize = c.AwgKcmil;
        }
    }
}
