# AutoCAD Electrical Project DB — .NET Palette Plugin

Dockable WPF palette for AutoCAD that front-ends the SQLite electrical project database.
Browse catalogs, view and edit project records, and push records into the drawing — all
inside a panel docked next to the drawing area.

---

## Requirements

| Item | Minimum version |
|------|----------------|
| AutoCAD | 2019 (v23) — required for `PaletteSet.AddVisual()` WPF hosting |
| .NET Framework | 4.8 (ships with AutoCAD 2019+) |
| Visual Studio | 2019 or 2022 (or `dotnet build` CLI) |
| SQLite database | Created by the Python CLI (`python cli.py init ...`) |

---

## Project Structure

```
plugin/
├── AutoCAD_Database_Plugin.csproj
├── Commands/
│   └── EpdbCommand.cs          IExtensionApplication + [CommandMethod] EPDB / EPDBSET
├── Data/
│   ├── Models.cs               C# POCOs for all DB tables (CLASS A + CLASS B)
│   ├── DbContext.cs            ADO.NET async query layer (parameterized, no EF)
│   └── PluginSettings.cs       Registry persistence for the DB file path
├── ViewModels/
│   ├── ViewModelBase.cs        INotifyPropertyChanged base
│   ├── RelayCommand.cs         ICommand (sync + async variants)
│   ├── MainViewModel.cs        Root VM — project list, tab VMs
│   ├── CatalogTabViewModel.cs  Catalog browser
│   ├── EquipmentTabViewModel.cs CRUD for equipment tab
│   ├── InstrumentsTabViewModel.cs CRUD for instruments tab
│   ├── CablesTabViewModel.cs   CRUD for cables tab
│   └── RecordEntryViewModel.cs Shared Add/Edit modal VM
├── Views/
│   ├── Converters.cs           BoolToVisibility, NullToVisibility
│   ├── EpdbPalette.xaml(.cs)   Main 5-tab palette UserControl
│   └── RecordEntryWindow.xaml(.cs) Modal add/edit window
└── Integration/
    └── DrawingIntegration.cs   Push DB records into AutoCAD drawing
```

---

## Build Instructions

### 1. Set the AutoCAD install path

The `.csproj` defaults to `C:\Program Files\Autodesk\AutoCAD 2025`.
Override per build if needed:

```powershell
dotnet build /p:AcadDir="C:\Program Files\Autodesk\AutoCAD 2024"
```

Or open the `.csproj` in Visual Studio, right-click the project →
**Properties → Build → Conditional Compilation Symbols** and set `AcadDir`.

### 2. Referenced AutoCAD assemblies (Copy Local = False)

| Assembly | Namespace | Purpose |
|----------|-----------|---------|
| `accoremgd.dll` | `Autodesk.AutoCAD.ApplicationServices` | Application, Document |
| `acdbmgd.dll`   | `Autodesk.AutoCAD.DatabaseServices`   | Transaction, Block, Table |
| `acmgd.dll`     | `Autodesk.AutoCAD.Runtime`            | CommandMethod, ExtensionApplication |
| `AcWindows.dll` | `Autodesk.AutoCAD.Windows`            | PaletteSet |

All four are in the AutoCAD install folder. **Do not copy them to the output** —
AutoCAD loads them into its process and the plugin shares the same AppDomain.

### 3. Build

```powershell
cd plugin
dotnet build -c Release
```

Output: `bin\Release\net48\AutoCAD_Database_Plugin.dll`

The `System.Data.SQLite.dll` and `SQLite.Interop.dll` (native, x64) are copied
to the output folder automatically by the NuGet package build targets.

---

## Loading in AutoCAD

```
Command: NETLOAD
```

Browse to `bin\Release\net48\AutoCAD_Database_Plugin.dll` and click **Open**.

AutoCAD will load the plugin and print:
```
Electrical Project DB plugin loaded. Type EPDB to open.
```

> **Tip:** Add a `NETLOAD` line to `acad.lsp` or the Startup Suite for auto-load.

---

## Commands

| Command   | Description |
|-----------|-------------|
| `EPDB`    | Open (or re-show) the Electrical Project DB palette |
| `EPDBSET` | Open a file browser to select the `.db` database file |

---

## Example Session

```
Command: EPDB
  → Palette opens on the right side of the screen

[Palette: Set DB... button]
  → Browse to acdb.db (created by: python cli.py init --project PRJ-001 ...)

[Palette: Project tab]
  → ComboBox now shows PRJ-001 — Water Treatment Facility
  → Project summary (client, NEC edition, voltage system) displayed

[Palette: Equipment tab]
  → DataGrid shows SWGR-1, MCC-1A
  → Click "Add" → RecordEntryWindow opens
  → Pick "Siemens SENTRON WL" from Equipment Catalog → Name pre-fills
  → Enter tag "MCC-2A", Bus Voltage 480, Fed From "SWGR-1"
  → Click OK → row appears in DataGrid

[Palette: Equipment tab → select MCC-2A → "Insert -> Drawing"]
  → AutoCAD prompts: [Block/Attributes/Table/Cancel]
  → Type B (Block) → pick insertion point in model space
  → Block reference inserted with attribute data from the DB record

[Palette: Cables tab]
  → DataGrid shows C-001 (SWGR-1 → MCC-1A, 85 ft)
  → Select C-001 → "Insert -> Drawing" → type T (Table)
  → Click an existing AutoCAD Table → row appended with cable data
```

---

## Drawing Integration Details

The **"Insert -> Drawing"** button in each editable tab offers three operations:

| Choice | What happens |
|--------|-------------|
| **Block** | Prompts for an insertion point; inserts a block reference. If the block definition doesn't exist yet, a placeholder is created with attribute definitions matching the record's fields. |
| **Attributes** | Prompts to select an existing block reference; writes matching record fields into its attribute values (matched by tag name). |
| **Table** | Prompts to select an AutoCAD `Table` object; appends a new row. Column mapping is done by matching the header row text (row 0) to field keys. Falls back to column position if headers don't match. |

Every drawing-database write is wrapped in `Transaction` + `DocumentLock`.

### Attribute tag → field mapping (Equipment)

| Attribute tag | DB field |
|---------------|----------|
| `TAG` | equipment.tag |
| `NAME` | equipment.name |
| `BUS_VOLTAGE_V` | equipment.bus_voltage_v |
| `FED_FROM_TAG` | equipment.fed_from_tag |
| `BREAKER_TRIP` | equipment.breaker_trip_a |
| `DRAWING_REF` | equipment.drawing_ref |
| `SHEET_NUMBER` | equipment.sheet_number |
| `ONE_LINE_REF` | equipment.one_line_ref |
| `STATUS` | equipment.status |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `EPDB` is unknown command | NETLOAD failed — check the Output window for errors |
| PaletteSet crashes on open | AutoCAD version < 2019; `AddVisual()` not available — wrap the UserControl in `ElementHost` and use `_ps.Add()` instead |
| "No database loaded" on open | Click **Set DB...** or run `EPDBSET` and browse to your `acdb.db` file |
| SQLite interop error | Ensure `SQLite.Interop.dll` (x64) is next to the plugin DLL; the NuGet package copies it automatically on build |
| Tables show no data | Run `python seed_catalogs.py` in the Python project first |
