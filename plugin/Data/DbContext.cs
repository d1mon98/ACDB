using System;
using System.Collections.Generic;
using System.Data;
using System.Threading.Tasks;
using System.Data.SQLite;

namespace AcDbPlugin.Data
{
    /// <summary>
    /// ADO.NET data access layer wrapping the SQLite electrical project database.
    /// All public methods are async (Task.Run-based) so callers never block the UI.
    /// All queries are fully parameterized.
    /// </summary>
    public class DbContext
    {
        private readonly string _cs;
        private readonly string _dbPath;

        public DbContext(string databasePath)
        {
            _dbPath = databasePath;
            _cs = $"Data Source={databasePath};Version=3;Foreign Keys=True;";
        }

        private SQLiteConnection OpenConnection()
        {
            var conn = new SQLiteConnection(_cs);
            conn.Open();
            return conn;
        }

        // ------------------------------------------------------------------ //
        // Projects
        // ------------------------------------------------------------------ //

        public Task<List<Project>> GetProjectsAsync() => Task.Run(() =>
        {
            var list = new List<Project>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM projects ORDER BY project_number", conn);
            using var r = cmd.ExecuteReader();
            while (r.Read()) list.Add(MapProject(r));
            return list;
        });

        private static Project MapProject(SQLiteDataReader r) => new Project
        {
            ProjectId        = r.GetInt32(r.GetOrdinal("project_id")),
            ProjectNumber    = Str(r, "project_number"),
            ProjectName      = Str(r, "project_name"),
            Client           = Str(r, "client"),
            Location         = Str(r, "location"),
            EngineerOfRecord = Str(r, "engineer_of_record"),
            IssueDate        = NullDate(r, "issue_date"),
            NecEdition       = Str(r, "nec_edition"),
            VoltageSystem    = Str(r, "voltage_system"),
            Notes            = Str(r, "notes"),
        };

        public Task<int> AddProjectAsync(Project p) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                INSERT INTO projects
                    (project_number, project_name, client, location,
                     engineer_of_record, issue_date, nec_edition, voltage_system, notes)
                VALUES
                    (@num, @name, @client, @loc, @eng, @date, @nec, @volt, @notes);
                SELECT last_insert_rowid();", conn);
            cmd.Parameters.AddWithValue("@num",    p.ProjectNumber ?? "");
            cmd.Parameters.AddWithValue("@name",   p.ProjectName ?? "");
            cmd.Parameters.AddWithValue("@client", p.Client ?? "");
            cmd.Parameters.AddWithValue("@loc",    p.Location ?? "");
            cmd.Parameters.AddWithValue("@eng",    p.EngineerOfRecord ?? "");
            cmd.Parameters.AddWithValue("@date",   p.IssueDate.HasValue ? (object)p.IssueDate.Value.ToString("yyyy-MM-dd") : DBNull.Value);
            cmd.Parameters.AddWithValue("@nec",    p.NecEdition ?? "");
            cmd.Parameters.AddWithValue("@volt",   p.VoltageSystem ?? "");
            cmd.Parameters.AddWithValue("@notes",  p.Notes ?? "");
            return Convert.ToInt32(cmd.ExecuteScalar());
        });

        public Task UpdateProjectAsync(Project p) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                UPDATE projects SET
                    project_number    = @num,
                    project_name      = @name,
                    client            = @client,
                    location          = @loc,
                    engineer_of_record= @eng,
                    issue_date        = @date,
                    nec_edition       = @nec,
                    voltage_system    = @volt,
                    notes             = @notes
                WHERE project_id = @id", conn);
            cmd.Parameters.AddWithValue("@num",    p.ProjectNumber ?? "");
            cmd.Parameters.AddWithValue("@name",   p.ProjectName ?? "");
            cmd.Parameters.AddWithValue("@client", p.Client ?? "");
            cmd.Parameters.AddWithValue("@loc",    p.Location ?? "");
            cmd.Parameters.AddWithValue("@eng",    p.EngineerOfRecord ?? "");
            cmd.Parameters.AddWithValue("@date",   p.IssueDate.HasValue ? (object)p.IssueDate.Value.ToString("yyyy-MM-dd") : DBNull.Value);
            cmd.Parameters.AddWithValue("@nec",    p.NecEdition ?? "");
            cmd.Parameters.AddWithValue("@volt",   p.VoltageSystem ?? "");
            cmd.Parameters.AddWithValue("@notes",  p.Notes ?? "");
            cmd.Parameters.AddWithValue("@id",     p.ProjectId);
            cmd.ExecuteNonQuery();
        });

        public Task DeleteProjectAsync(int projectId) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "DELETE FROM projects WHERE project_id = @id", conn);
            cmd.Parameters.AddWithValue("@id", projectId);
            cmd.ExecuteNonQuery();
        });

        // ------------------------------------------------------------------ //
        // Class A catalogs — generic DataTable for the Catalogs tab DataGrid
        // ------------------------------------------------------------------ //

        public Task<DataTable> GetCatalogTableAsync(string tableName) => Task.Run(() =>
        {
            // Whitelist prevents SQL injection via table name
            if (!AllowedCatalogs.Contains(tableName))
                throw new ArgumentException($"Unknown catalog table: {tableName}");

            using var conn = OpenConnection();
            using var da = new SQLiteDataAdapter($"SELECT * FROM {tableName}", conn);
            var dt = new DataTable(tableName);
            da.Fill(dt);
            return dt;
        });

        private static readonly HashSet<string> AllowedCatalogs =
            new HashSet<string> { "equip_catalog", "cable_catalog",
                                   "instrument_catalog", "conduit_catalog" };

        // Typed catalog lists — used by ComboBox pickers in the entry window

        public Task<List<EquipCatalog>> GetEquipCatalogAsync() => Task.Run(() =>
        {
            var list = new List<EquipCatalog>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM equip_catalog ORDER BY manufacturer, model", conn);
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                list.Add(new EquipCatalog
                {
                    EquipCatalogId   = r.GetInt32(r.GetOrdinal("equip_catalog_id")),
                    Manufacturer     = Str(r, "manufacturer"),
                    Model            = Str(r, "model"),
                    Description      = Str(r, "description"),
                    Type             = Str(r, "type"),
                    VoltageRatingV   = NullInt(r, "voltage_rating_v"),
                    CurrentRatingA   = NullDbl(r, "current_rating_a"),
                    IcRatingKa       = NullDbl(r, "ic_rating_ka"),
                    InterruptingType = Str(r, "interrupting_type"),
                    EnclosureNema    = Str(r, "enclosure_nema"),
                    WeightLbs        = NullDbl(r, "weight_lbs"),
                    Notes            = Str(r, "notes"),
                });
            }
            return list;
        });

        public Task<List<CableCatalog>> GetCableCatalogAsync() => Task.Run(() =>
        {
            var list = new List<CableCatalog>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM cable_catalog ORDER BY manufacturer, trade_name", conn);
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                list.Add(new CableCatalog
                {
                    CableCatalogId    = r.GetInt32(r.GetOrdinal("cable_catalog_id")),
                    Manufacturer      = Str(r, "manufacturer"),
                    TradeName         = Str(r, "trade_name"),
                    Type              = Str(r, "type"),
                    ConductorMaterial = Str(r, "conductor_material"),
                    Insulation        = Str(r, "insulation"),
                    VoltageRatingV    = NullInt(r, "voltage_rating_v"),
                    NumConductors     = NullInt(r, "num_conductors"),
                    AwgKcmil          = Str(r, "awg_kcmil"),
                    Shield            = Str(r, "shield") == "1" || Str(r, "shield") == "True",
                    Armor             = Str(r, "armor") == "1" || Str(r, "armor") == "True",
                    AmpacityConduitA  = NullDbl(r, "ampacity_conduit_a"),
                    AmpacityTrayA     = NullDbl(r, "ampacity_tray_a"),
                    OdInches          = NullDbl(r, "od_inches"),
                    WeightLbft        = NullDbl(r, "weight_lbft"),
                    Notes             = Str(r, "notes"),
                });
            }
            return list;
        });

        public Task<List<InstrumentCatalog>> GetInstrumentCatalogAsync() => Task.Run(() =>
        {
            var list = new List<InstrumentCatalog>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM instrument_catalog ORDER BY manufacturer, model", conn);
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                list.Add(new InstrumentCatalog
                {
                    InstrumentCatalogId = r.GetInt32(r.GetOrdinal("instrument_catalog_id")),
                    Manufacturer        = Str(r, "manufacturer"),
                    Model               = Str(r, "model"),
                    Description         = Str(r, "description"),
                    Type                = Str(r, "type"),
                    SignalType          = Str(r, "signal_type"),
                    SupplyVdc           = NullDbl(r, "supply_vdc"),
                    EnclosureNema       = Str(r, "enclosure_nema"),
                    HazardousAreaRating = Str(r, "hazardous_area_rating"),
                    Notes               = Str(r, "notes"),
                });
            }
            return list;
        });

        // ------------------------------------------------------------------ //
        // Equipment
        // ------------------------------------------------------------------ //

        public Task<List<Equipment>> GetEquipmentAsync(int projectId) => Task.Run(() =>
        {
            var list = new List<Equipment>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM equipment WHERE project_id=@pid ORDER BY tag", conn);
            cmd.Parameters.AddWithValue("@pid", projectId);
            using var r = cmd.ExecuteReader();
            while (r.Read()) list.Add(MapEquipment(r));
            return list;
        });

        private static Equipment MapEquipment(SQLiteDataReader r) => new Equipment
        {
            EquipId        = r.GetInt32(r.GetOrdinal("equip_id")),
            ProjectId      = r.GetInt32(r.GetOrdinal("project_id")),
            EquipCatalogId = NullInt(r, "equip_catalog_id"),
            Tag            = Str(r, "tag"),
            Name           = Str(r, "name"),
            BusVoltageV    = NullInt(r, "bus_voltage_v"),
            RatedCurrentA  = NullDbl(r, "rated_current_a"),
            IcRatingKa     = NullDbl(r, "ic_rating_ka"),
            FedFromTag     = Str(r, "fed_from_tag"),
            BreakerTripA   = NullDbl(r, "breaker_trip_a"),
            BreakerFrameA  = NullDbl(r, "breaker_frame_a"),
            DrawingRef     = Str(r, "drawing_ref"),
            SheetNumber    = Str(r, "sheet_number"),
            OneLineRef     = Str(r, "one_line_ref"),
            Status         = Str(r, "status"),
            Notes          = Str(r, "notes"),
        };

        public Task<int> AddEquipmentAsync(Equipment e) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                INSERT INTO equipment
                    (project_id,equip_catalog_id,tag,name,bus_voltage_v,
                     rated_current_a,ic_rating_ka,fed_from_tag,breaker_trip_a,
                     breaker_frame_a,drawing_ref,sheet_number,one_line_ref,status,notes)
                VALUES
                    (@pid,@cat,@tag,@name,@bv,
                     @ra,@ic,@ff,@bt,
                     @bf,@dr,@sn,@olr,@st,@notes);
                SELECT last_insert_rowid();", conn);
            BindEquip(cmd, e);
            return Convert.ToInt32(cmd.ExecuteScalar());
        });

        public Task UpdateEquipmentAsync(Equipment e) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                UPDATE equipment SET
                    equip_catalog_id=@cat,tag=@tag,name=@name,bus_voltage_v=@bv,
                    rated_current_a=@ra,ic_rating_ka=@ic,fed_from_tag=@ff,
                    breaker_trip_a=@bt,breaker_frame_a=@bf,drawing_ref=@dr,
                    sheet_number=@sn,one_line_ref=@olr,status=@st,notes=@notes
                WHERE equip_id=@id", conn);
            BindEquip(cmd, e);
            cmd.Parameters.AddWithValue("@id", e.EquipId);
            cmd.ExecuteNonQuery();
        });

        public Task DeleteEquipmentAsync(int id) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand("DELETE FROM equipment WHERE equip_id=@id", conn);
            cmd.Parameters.AddWithValue("@id", id);
            cmd.ExecuteNonQuery();
        });

        private static void BindEquip(SQLiteCommand c, Equipment e)
        {
            c.Parameters.AddWithValue("@pid",   e.ProjectId);
            c.Parameters.AddWithValue("@cat",   N(e.EquipCatalogId));
            c.Parameters.AddWithValue("@tag",   e.Tag.ToUpperInvariant());
            c.Parameters.AddWithValue("@name",  e.Name);
            c.Parameters.AddWithValue("@bv",    N(e.BusVoltageV));
            c.Parameters.AddWithValue("@ra",    N(e.RatedCurrentA));
            c.Parameters.AddWithValue("@ic",    N(e.IcRatingKa));
            c.Parameters.AddWithValue("@ff",    Up(e.FedFromTag));
            c.Parameters.AddWithValue("@bt",    N(e.BreakerTripA));
            c.Parameters.AddWithValue("@bf",    N(e.BreakerFrameA));
            c.Parameters.AddWithValue("@dr",    e.DrawingRef);
            c.Parameters.AddWithValue("@sn",    e.SheetNumber);
            c.Parameters.AddWithValue("@olr",   e.OneLineRef);
            c.Parameters.AddWithValue("@st",    e.Status);
            c.Parameters.AddWithValue("@notes", e.Notes);
        }

        // ------------------------------------------------------------------ //
        // Instruments
        // ------------------------------------------------------------------ //

        public Task<List<Instrument>> GetInstrumentsAsync(int projectId) => Task.Run(() =>
        {
            var list = new List<Instrument>();
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM instruments WHERE project_id=@pid ORDER BY tag", conn);
            cmd.Parameters.AddWithValue("@pid", projectId);
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                list.Add(new Instrument
                {
                    InstrumentId        = r.GetInt32(r.GetOrdinal("instrument_id")),
                    ProjectId           = r.GetInt32(r.GetOrdinal("project_id")),
                    InstrumentCatalogId = NullInt(r, "instrument_catalog_id"),
                    Tag                 = Str(r, "tag"),
                    ServiceDescription  = Str(r, "service_description"),
                    LoopNumber          = Str(r, "loop_number"),
                    PAndIdRef           = Str(r, "p_and_id_ref"),
                    PanelTag            = Str(r, "panel_tag"),
                    SignalType          = Str(r, "signal_type"),
                    SupplySourceTag     = Str(r, "supply_source_tag"),
                    DrawingRef          = Str(r, "drawing_ref"),
                    SheetNumber         = Str(r, "sheet_number"),
                    Status              = Str(r, "status"),
                    Notes               = Str(r, "notes"),
                });
            }
            return list;
        });

        public Task<int> AddInstrumentAsync(Instrument inst) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                INSERT INTO instruments
                    (project_id,instrument_catalog_id,tag,service_description,
                     loop_number,p_and_id_ref,panel_tag,signal_type,
                     supply_source_tag,drawing_ref,sheet_number,status,notes)
                VALUES
                    (@pid,@cat,@tag,@svc,
                     @ln,@pir,@pt,@sig,
                     @sst,@dr,@sn,@st,@notes);
                SELECT last_insert_rowid();", conn);
            BindInstr(cmd, inst);
            return Convert.ToInt32(cmd.ExecuteScalar());
        });

        public Task UpdateInstrumentAsync(Instrument inst) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                UPDATE instruments SET
                    instrument_catalog_id=@cat,tag=@tag,service_description=@svc,
                    loop_number=@ln,p_and_id_ref=@pir,panel_tag=@pt,signal_type=@sig,
                    supply_source_tag=@sst,drawing_ref=@dr,sheet_number=@sn,
                    status=@st,notes=@notes
                WHERE instrument_id=@id", conn);
            BindInstr(cmd, inst);
            cmd.Parameters.AddWithValue("@id", inst.InstrumentId);
            cmd.ExecuteNonQuery();
        });

        public Task DeleteInstrumentAsync(int id) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "DELETE FROM instruments WHERE instrument_id=@id", conn);
            cmd.Parameters.AddWithValue("@id", id);
            cmd.ExecuteNonQuery();
        });

        private static void BindInstr(SQLiteCommand c, Instrument i)
        {
            c.Parameters.AddWithValue("@pid",   i.ProjectId);
            c.Parameters.AddWithValue("@cat",   N(i.InstrumentCatalogId));
            c.Parameters.AddWithValue("@tag",   i.Tag.ToUpperInvariant());
            c.Parameters.AddWithValue("@svc",   i.ServiceDescription);
            c.Parameters.AddWithValue("@ln",    i.LoopNumber);
            c.Parameters.AddWithValue("@pir",   i.PAndIdRef);
            c.Parameters.AddWithValue("@pt",    Up(i.PanelTag));
            c.Parameters.AddWithValue("@sig",   i.SignalType);
            c.Parameters.AddWithValue("@sst",   Up(i.SupplySourceTag));
            c.Parameters.AddWithValue("@dr",    i.DrawingRef);
            c.Parameters.AddWithValue("@sn",    i.SheetNumber);
            c.Parameters.AddWithValue("@st",    i.Status);
            c.Parameters.AddWithValue("@notes", i.Notes);
        }

        // ------------------------------------------------------------------ //
        // Cables
        // ------------------------------------------------------------------ //

        public Task<List<Cable>> GetCablesAsync(int projectId) => Task.Run(() =>
        {
            var list = new List<Cable>();
            using var conn = OpenConnection();
            const string sql = @"
                SELECT c.*,
                       COALESCE(fe.tag, fi.tag) AS from_tag,
                       COALESCE(te.tag, ti.tag) AS to_tag
                FROM cables c
                LEFT JOIN equipment   fe ON c.from_equipment_id   = fe.equip_id
                LEFT JOIN instruments fi ON c.from_instrument_id  = fi.instrument_id
                LEFT JOIN equipment   te ON c.to_equipment_id     = te.equip_id
                LEFT JOIN instruments ti ON c.to_instrument_id    = ti.instrument_id
                WHERE c.project_id = @pid
                ORDER BY c.cable_tag";
            using var cmd = new SQLiteCommand(sql, conn);
            cmd.Parameters.AddWithValue("@pid", projectId);
            using var r = cmd.ExecuteReader();
            while (r.Read())
            {
                list.Add(new Cable
                {
                    CableId                = r.GetInt32(r.GetOrdinal("cable_id")),
                    ProjectId              = r.GetInt32(r.GetOrdinal("project_id")),
                    CableCatalogId         = NullInt(r, "cable_catalog_id"),
                    CableTag               = Str(r, "cable_tag"),
                    ServiceDescription     = Str(r, "service_description"),
                    FromEquipmentId        = NullInt(r, "from_equipment_id"),
                    FromInstrumentId       = NullInt(r, "from_instrument_id"),
                    FromTerminal           = Str(r, "from_terminal"),
                    ToEquipmentId          = NullInt(r, "to_equipment_id"),
                    ToInstrumentId         = NullInt(r, "to_instrument_id"),
                    ToTerminal             = Str(r, "to_terminal"),
                    ConduitTag             = Str(r, "conduit_tag"),
                    RoutingDescription     = Str(r, "routing_description"),
                    LengthFt               = NullDbl(r, "length_ft"),
                    LengthFtActual         = NullDbl(r, "length_ft_actual"),
                    NumConductorsUsed      = NullInt(r, "num_conductors_used"),
                    ConductorSizeAwgKcmil  = Str(r, "conductor_size_awg_kcmil"),
                    VoltageDropPct         = NullDbl(r, "voltage_drop_pct"),
                    DrawingRef             = Str(r, "drawing_ref"),
                    SheetNumber            = Str(r, "sheet_number"),
                    Status                 = Str(r, "status"),
                    Notes                  = Str(r, "notes"),
                    FromTag                = Str(r, "from_tag"),
                    ToTag                  = Str(r, "to_tag"),
                });
            }
            return list;
        });

        public Task<int> AddCableAsync(Cable c) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                INSERT INTO cables
                    (project_id,cable_catalog_id,cable_tag,service_description,
                     from_equipment_id,from_instrument_id,from_terminal,
                     to_equipment_id,to_instrument_id,to_terminal,
                     conduit_tag,routing_description,length_ft,length_ft_actual,
                     num_conductors_used,conductor_size_awg_kcmil,
                     voltage_drop_pct,drawing_ref,sheet_number,status,notes)
                VALUES
                    (@pid,@cat,@tag,@svc,
                     @feq,@finstr,@fterm,
                     @teq,@tinstr,@tterm,
                     @ct,@rd,@lft,@lfta,
                     @nc,@cs,
                     @vd,@dr,@sn,@st,@notes);
                SELECT last_insert_rowid();", conn);
            BindCable(cmd, c);
            return Convert.ToInt32(cmd.ExecuteScalar());
        });

        public Task UpdateCableAsync(Cable c) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(@"
                UPDATE cables SET
                    cable_catalog_id=@cat,cable_tag=@tag,service_description=@svc,
                    from_equipment_id=@feq,from_instrument_id=@finstr,from_terminal=@fterm,
                    to_equipment_id=@teq,to_instrument_id=@tinstr,to_terminal=@tterm,
                    conduit_tag=@ct,routing_description=@rd,
                    length_ft=@lft,length_ft_actual=@lfta,
                    num_conductors_used=@nc,conductor_size_awg_kcmil=@cs,
                    voltage_drop_pct=@vd,drawing_ref=@dr,sheet_number=@sn,
                    status=@st,notes=@notes
                WHERE cable_id=@id", conn);
            BindCable(cmd, c);
            cmd.Parameters.AddWithValue("@id", c.CableId);
            cmd.ExecuteNonQuery();
        });

        public Task DeleteCableAsync(int id) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand("DELETE FROM cables WHERE cable_id=@id", conn);
            cmd.Parameters.AddWithValue("@id", id);
            cmd.ExecuteNonQuery();
        });

        private static void BindCable(SQLiteCommand c, Cable b)
        {
            c.Parameters.AddWithValue("@pid",    b.ProjectId);
            c.Parameters.AddWithValue("@cat",    N(b.CableCatalogId));
            c.Parameters.AddWithValue("@tag",    b.CableTag.ToUpperInvariant());
            c.Parameters.AddWithValue("@svc",    b.ServiceDescription);
            c.Parameters.AddWithValue("@feq",    N(b.FromEquipmentId));
            c.Parameters.AddWithValue("@finstr", N(b.FromInstrumentId));
            c.Parameters.AddWithValue("@fterm",  b.FromTerminal);
            c.Parameters.AddWithValue("@teq",    N(b.ToEquipmentId));
            c.Parameters.AddWithValue("@tinstr", N(b.ToInstrumentId));
            c.Parameters.AddWithValue("@tterm",  b.ToTerminal);
            c.Parameters.AddWithValue("@ct",     Up(b.ConduitTag));
            c.Parameters.AddWithValue("@rd",     b.RoutingDescription);
            c.Parameters.AddWithValue("@lft",    N(b.LengthFt));
            c.Parameters.AddWithValue("@lfta",   N(b.LengthFtActual));
            c.Parameters.AddWithValue("@nc",     N(b.NumConductorsUsed));
            c.Parameters.AddWithValue("@cs",     b.ConductorSizeAwgKcmil);
            c.Parameters.AddWithValue("@vd",     N(b.VoltageDropPct));
            c.Parameters.AddWithValue("@dr",     b.DrawingRef);
            c.Parameters.AddWithValue("@sn",     b.SheetNumber);
            c.Parameters.AddWithValue("@st",     b.Status);
            c.Parameters.AddWithValue("@notes",  b.Notes);
        }

        // ------------------------------------------------------------------ //
        // Helpers
        // ------------------------------------------------------------------ //

        private static string Str(SQLiteDataReader r, string col)
        {
            int ord = r.GetOrdinal(col);
            return r.IsDBNull(ord) ? "" : r.GetString(ord);
        }

        private static int? NullInt(SQLiteDataReader r, string col)
        {
            int ord = r.GetOrdinal(col);
            return r.IsDBNull(ord) ? (int?)null : r.GetInt32(ord);
        }

        private static double? NullDbl(SQLiteDataReader r, string col)
        {
            int ord = r.GetOrdinal(col);
            return r.IsDBNull(ord) ? (double?)null : r.GetDouble(ord);
        }

        private static DateTime? NullDate(SQLiteDataReader r, string col)
        {
            int ord = r.GetOrdinal(col);
            if (r.IsDBNull(ord)) return null;
            return DateTime.TryParse(r.GetString(ord), out var d) ? d : (DateTime?)null;
        }

        // ------------------------------------------------------------------ //
        // Equipment by ID — used by LinkedBlockService refresh
        // ------------------------------------------------------------------ //

        public Equipment? GetEquipmentById(int id)
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM equipment WHERE equip_id = @id LIMIT 1", conn);
            cmd.Parameters.AddWithValue("@id", id);
            using var r = cmd.ExecuteReader();
            return r.Read() ? MapEquipment(r) : null;
        }

        public Task<Equipment?> GetEquipmentByIdAsync(int id) =>
            Task.Run(() => GetEquipmentById(id));

        // Returns the file's last-write timestamp — cheapest change-detection for the poller.
        public DateTime GetDbLastModified() =>
            System.IO.File.Exists(_dbPath)
                ? System.IO.File.GetLastWriteTime(_dbPath)
                : DateTime.MinValue;

        // ------------------------------------------------------------------ //
        // Tag-based lookups (used when resolving cable FROM/TO endpoints)
        // ------------------------------------------------------------------ //

        public Task<Equipment?> FindEquipmentByTagAsync(int projectId, string tag) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM equipment WHERE project_id=@pid AND upper(tag)=upper(@tag) LIMIT 1",
                conn);
            cmd.Parameters.AddWithValue("@pid", projectId);
            cmd.Parameters.AddWithValue("@tag", tag.Trim());
            using var r = cmd.ExecuteReader();
            return r.Read() ? MapEquipment(r) : (Equipment?)null;
        });

        public Task<Instrument?> FindInstrumentByTagAsync(int projectId, string tag) => Task.Run(() =>
        {
            using var conn = OpenConnection();
            using var cmd = new SQLiteCommand(
                "SELECT * FROM instruments WHERE project_id=@pid AND upper(tag)=upper(@tag) LIMIT 1",
                conn);
            cmd.Parameters.AddWithValue("@pid", projectId);
            cmd.Parameters.AddWithValue("@tag", tag.Trim());
            using var r = cmd.ExecuteReader();
            if (!r.Read()) return (Instrument?)null;
            return new Instrument
            {
                InstrumentId        = r.GetInt32(r.GetOrdinal("instrument_id")),
                ProjectId           = r.GetInt32(r.GetOrdinal("project_id")),
                InstrumentCatalogId = NullInt(r, "instrument_catalog_id"),
                Tag                 = Str(r, "tag"),
                ServiceDescription  = Str(r, "service_description"),
                Status              = Str(r, "status"),
            };
        });

        // Box a nullable value; return DBNull if null
        private static object N<T>(T? val) where T : struct =>
            val.HasValue ? (object)val.Value : DBNull.Value;

        // Uppercase a string; return DBNull if empty
        private static object Up(string? s) =>
            string.IsNullOrWhiteSpace(s) ? (object)DBNull.Value : s.ToUpperInvariant();
    }
}
