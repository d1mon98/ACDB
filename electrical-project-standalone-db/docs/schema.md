# Schema Reference — Electrical Project Standalone DB

This document is the full table, field and relationship reference. The database
is designed to fully and accurately reflect an industrial electrical and I&C
project for U.S. industrial, water/wastewater and process work.

---

## 1. Two classes of tables

Every table belongs to exactly one of two classes.

### Class A — General Catalogs

Permanent, project-independent reference data — a reusable library of
manufacturer equipment, standard cable types, instrument models and so on. A
catalog row is the **single source of truth** for the permanent attributes of
the thing it describes.

| Table | Holds |
|-------|-------|
| `catalog_manufacturers` | Manufacturer / vendor list |
| `catalog_equipment` | Standard power-distribution equipment models |
| `catalog_cables` | Standard cable / conductor types |
| `catalog_instruments` | Standard field instrument models |
| `catalog_io_modules` | Standard PLC / RIO I/O modules |
| `catalog_devices` | Standard control / protection devices |

### Class B — Project Tables

The actual equipment, tags, locations and connections of **one** project. Every
Class B row carries a `project_id`.

| Table | Module | Holds |
|-------|--------|-------|
| `projects` | Projects | The project registry |
| `project_locations` | Locations / Areas | Areas, rooms, buildings (hierarchical) |
| `project_feeders` | Power Distribution | Feeder / one-line schedule |
| `project_equipment` | Equipment | Power-distribution equipment instances |
| `project_control_panels` | Control Panels | Control / instrumentation panels |
| `project_panel_components` | Panel Components | Devices inside a control panel |
| `project_panel_circuits` | Panel Circuits | Circuits within panelboards & MCCs |
| `project_cables` | Cables | Cable instances (FROM-TO schedule) |
| `project_cable_routes` | Cable Routes | Named cable routing paths |
| `project_conduits` | Conduits / Trays | Conduit, tray & duct-bank segments |
| `project_instruments` | Instruments | Field instrument instances |
| `project_io_list` | I/O List | Instruments/devices ↔ PLC points |
| `project_terminal_blocks` | Terminal Blocks | Terminal-strip points |
| `project_terminations` | Terminations | Cable-end terminations |
| `project_network_devices` | Network Devices | Switches, gateways, etc. |
| `project_drawings` | Drawings | Drawing register |
| `project_calculations` | Calculations | Calculation register |
| `project_qaqc_checks` | QA/QC Checks | QA/QC check register |

> A third level — **Project Catalogs** (a per-project approved subset of the
> global catalogs) — is planned as a later phase. Today, project tables link
> directly to the global catalogs.

---

## 2. The Merge Principle

A Class B row in a *catalog-linked* table is created by **merging a catalog
record (permanent data) with project-specific data**. The merge is a **nullable
foreign key** from the project row to the catalog row — never a copy of the
catalog's columns.

The five catalog-linked tables also support a **custom / one-off path**: the
catalog FK is left `NULL` and the permanent attributes go into `local_*`
columns. A named CHECK constraint guarantees a row always has one or the other:

| Project table | Catalog FK | Catalog table | Required local field (custom) |
|---------------|-----------|---------------|-------------------------------|
| `project_equipment` | `catalog_equipment_id` | `catalog_equipment` | `local_model` |
| `project_cables` | `catalog_cable_id` | `catalog_cables` | `local_cable_type_code` |
| `project_instruments` | `catalog_instrument_id` | `catalog_instruments` | `local_model` |
| `project_io_list` | `catalog_io_module_id` | `catalog_io_modules` | `local_io_module_model` |
| `project_panel_components` | `catalog_device_id` | `catalog_devices` | `local_model` |

The other nine project tables have no catalog merge — they are plain project
tables.

---

## 3. Conventions

Every table has these four columns (the `CommonMixin`): `id` (PK), `notes`
(free text), `created_at`, `updated_at`. They are omitted from the field lists
below.

All types are standard SQLAlchemy types, so the schema is PostgreSQL-portable.
Enum columns render as portable `VARCHAR` + `CHECK` (`native_enum=False`).

---

## 4. Enumerations

| Enum | Values |
|------|--------|
| `EquipmentCategory` | SWITCHGEAR, PANELBOARD, MCC, TRANSFORMER, VFD, ATS, DISCONNECT, OTHER |
| `ConductorMaterial` | CU, AL |
| `InstrumentType` | PRESSURE, FLOW, LEVEL, TEMPERATURE, ANALYTICAL, POSITION, OTHER |
| `IOType` | AI, AO, DI, DO, RTD, TC, COMM, OTHER |
| `DeviceCategory` | RELAY, PLC_CPU, HMI, POWER_SUPPLY, CIRCUIT_BREAKER, TERMINAL_BLOCK, SURGE_PROTECTOR, NETWORK_SWITCH, OTHER |
| `ProjectStatus` | PLANNING, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED |
| `IssueStage` | CONCEPT, PRELIMINARY, DESIGN_30, DESIGN_60, DESIGN_90, IFC, AS_BUILT, OTHER |
| `IndoorOutdoor` | INDOOR, OUTDOOR |
| `UL508AStatus` | LISTED, NOT_LISTED, PENDING, NOT_APPLICABLE |
| `RouteType` | TRAY, CONDUIT, DUCTBANK, DIRECT_BURIED, FREE_AIR, OTHER |
| `ConduitType` | CONDUIT, CABLE_TRAY, DUCTBANK, WIREWAY |
| `ConduitMaterial` | PVC, RMC, EMT, IMC, ALUMINUM, GALV_STEEL, FIBERGLASS, OTHER |
| `CableEnd` | FROM, TO |
| `TerminationType` | LUG, RING, FERRULE, TERMINAL_BLOCK, SPLICE, DIRECT, OTHER |
| `NetworkDeviceType` | SWITCH, ROUTER, GATEWAY, FIREWALL, ACCESS_POINT, MEDIA_CONVERTER, OTHER |
| `NetworkProtocol` | ETHERNET_IP, MODBUS_TCP, PROFINET, OPC_UA, DNP3, BACNET, OTHER |
| `DrawingType` | ONE_LINE, SCHEMATIC, PANEL_LAYOUT, LOOP_DIAGRAM, PID, LOCATION_PLAN, CABLE_ROUTING, DETAIL, OTHER |
| `DrawingStatus` | PRELIMINARY, IFR, IFA, IFB, IFC, AS_BUILT, OTHER |
| `CalcType` | LOAD, VOLTAGE_DROP, SHORT_CIRCUIT, CONDUIT_FILL, GROUNDING, LIGHTING, CABLE_AMPACITY, ARC_FLASH, OTHER |
| `CalcStatus` | PRELIMINARY, IN_PROGRESS, COMPLETE, CHECKED, APPROVED, OTHER |
| `QAQCCategory` | TAGGING, POWER, CABLES, INSTRUMENTS, IO, TERMINATIONS, DRAWINGS, GENERAL, OTHER |
| `QAQCStatus` | OPEN, PASS, FAIL, NOT_APPLICABLE, RESOLVED |
| `QAQCSeverity` | CRITICAL, MAJOR, MINOR |
| `AlarmPriority` | CRITICAL, HIGH, MEDIUM, LOW, NONE |

---

## 5. Class A — Catalog tables

**`catalog_manufacturers`** — `name` (req, unique), `abbreviation`, `country`.

**`catalog_equipment`** — `manufacturer_id` (FK), `category` (enum, req),
`model_series` (req), `rated_voltage`, `rated_current`, `rated_kva`,
`sccr_rating`, `enclosure_type`, `poles`, `phases`, `description`.

**`catalog_cables`** — `cable_type_code` (req, unique), `conductor_material`
(enum), `insulation_type`, `voltage_rating`, `conductor_count`,
`conductor_size`, `ampacity`, `shielded`, `armored`, `description`.

**`catalog_instruments`** — `manufacturer_id` (FK), `instrument_type` (enum,
req), `measurement_principle`, `model_series` (req), `signal_type`,
`process_connection`, `accuracy`, `power_requirement`, `area_classification`,
`description`.

**`catalog_io_modules`** — `manufacturer_id` (FK), `module_model` (req),
`io_type` (enum, req), `point_count`, `signal_range`, `description`.

**`catalog_devices`** — `manufacturer_id` (FK), `device_category` (enum, req),
`model` (req), `ratings`, `description`.

All `manufacturer_id` FKs are `ON DELETE RESTRICT`.

---

## 6. Class B — Project tables

Every Class B table has `project_id` → `projects` (`ON DELETE RESTRICT`). It is
omitted from the field lists below. `req` = required; `FK` = foreign key.

### 6.1 `projects`
`project_number` (req, unique), `name` (req), `client`, `facility`, `location`,
`voltage_system`, `issue_stage` (enum), `description`, `status` (enum, req).

### 6.2 `project_locations`
`location_code` (req, unique per project), `building`, `room`, `area`,
`process_system`, `indoor_outdoor` (enum), `area_classification` (hazardous
classification), `parent_location_id` (FK self, SET NULL), `description`.

### 6.3 `project_feeders` — Power Distribution
`feeder_tag` (req, unique per project), `source_equipment_id` (FK equipment),
`load_equipment_id` (FK equipment), `voltage`, `phases`, `ampacity`,
`ocpd_type`, `ocpd_rating`, `feeder_cable_id` (FK cables), `drawing_reference`,
`description`.

### 6.4 `project_equipment` *(catalog-linked)*
`catalog_equipment_id` (FK, RESTRICT), `equipment_tag` (req, unique per
project), `equipment_type`, `location_id` (FK locations), `voltage`, `phase`,
`hp_kw`, `fla`, `fed_from_id` (FK self — one-line topology), `feeder_cable_id`
(FK cables), `drawing_reference`, `project_settings`, `description`. Local:
`local_manufacturer`, `local_category` (enum), `local_model`,
`local_rated_voltage`, `local_rated_current`.
CHECK: `catalog_equipment_id` OR `local_model`.

### 6.5 `project_control_panels`
`panel_tag` (req, unique per project), `panel_type`, `voltage`,
`enclosure_type`, `sccr`, `manufacturer`, `ul508a_status` (enum), `location_id`
(FK locations), `description`.

### 6.6 `project_panel_components` *(catalog-linked)*
`control_panel_id` (FK control panels, req, RESTRICT), `catalog_device_id` (FK,
RESTRICT), `component_tag`, `component_type`, `part_number`, `voltage`,
`power_supply_source`, `terminal_block_reference`, `mounting_reference`,
`quantity` (req, default 1), `description`. Local: `local_manufacturer`,
`local_device_category` (enum), `local_model`, `local_ratings`.
CHECK: `catalog_device_id` OR `local_model`.

### 6.7 `project_panel_circuits`
`panel_id` (FK equipment, req, RESTRICT), `circuit_number` (req, unique per
panel), `load_description`, `connected_load`, `phases`, `breaker_size`,
`cable_id` (FK cables), `destination_equipment_id` (FK equipment).

### 6.8 `project_cables` *(catalog-linked)*
`catalog_cable_id` (FK, RESTRICT), `cable_tag` (req, unique per project),
`from_equipment_id`, `to_equipment_id`, `from_location_id`, `to_location_id`
(FKs), `length`, `routing` (free text), `route_id` (FK cable routes),
`voltage_class`, `drawing_reference`, `description`. Local:
`local_cable_type_code`, `local_conductor_material` (enum),
`local_conductor_size`, `local_conductor_count`, `local_insulation_type`,
`local_voltage_rating`.
CHECK: `catalog_cable_id` OR `local_cable_type_code`.

### 6.9 `project_cable_routes`
`route_tag` (req, unique per project), `route_type` (enum),
`from_location_id`, `to_location_id` (FK locations), `total_length`,
`description`.

### 6.10 `project_conduits` — Conduits / Trays
`conduit_tag` (req, unique per project), `conduit_type` (enum), `trade_size`,
`material` (enum), `route_id` (FK cable routes), `from_location_id`,
`to_location_id` (FK locations), `length`, `fill_percent`, `description`.

### 6.11 `project_instruments` *(catalog-linked)*
`catalog_instrument_id` (FK, RESTRICT), `instrument_tag` (req ISA tag, unique
per project), `location_id` (FK locations), `measured_variable`,
`pid_reference`, `loop_number`, `calibrated_range`, `set_point`,
`power_source`, `process_connection`, `associated_equipment_id` (FK equipment),
`cable_id` (FK cables), `plc_panel_id` (FK control panels), `description`.
Local: `local_manufacturer`, `local_instrument_type` (enum), `local_model`,
`local_signal_type`, `local_accuracy`.
CHECK: `catalog_instrument_id` OR `local_model`.

### 6.12 `project_io_list` *(catalog-linked)*
`catalog_io_module_id` (FK, RESTRICT), `io_tag`, `project_instrument_id` (FK
instruments), `project_panel_component_id` (FK panel components), `io_type`
(enum, req), `plc_panel_id` (FK control panels), `rack`, `slot`, `channel`,
`plc_address`, `signal_range`, `fail_state`, `alarm_priority` (enum),
`scada_tag`, `cable_id` (FK cables), `description`. Local:
`local_io_module_model`.
CHECK: `catalog_io_module_id` OR `local_io_module_model`.

### 6.13 `project_terminal_blocks`
`control_panel_id` (FK control panels), `terminal_strip` (req),
`terminal_number` (req), `wire_number`, `cable_id` (FK cables),
`conductor_core`, `device_tag`, `signal_description`, `description`.

### 6.14 `project_terminations`
`cable_id` (FK cables, req, RESTRICT), `cable_end` (enum), `conductor_core`,
`termination_type` (enum), `equipment_id` (FK equipment), `terminal_block_id`
(FK terminal blocks), `device_tag`, `drawing_reference`, `description`.

### 6.15 `project_network_devices`
`device_tag` (req, unique per project), `device_type` (enum), `manufacturer`,
`model`, `ip_address`, `subnet_mask`, `protocol` (enum), `port_count`,
`location_id` (FK locations), `control_panel_id` (FK control panels),
`description`.

### 6.16 `project_drawings`
`drawing_number` (req, unique per project), `title`, `drawing_type` (enum),
`revision`, `status` (enum), `discipline`, `sheet_size`, `scale`,
`description`.

### 6.17 `project_calculations`
`calc_number` (req, unique per project), `title`, `calc_type` (enum),
`revision`, `status` (enum), `result_summary`, `performed_by`, `description`.

### 6.18 `project_qaqc_checks`
`check_item` (req), `category` (enum), `severity` (enum), `status` (enum, req,
default OPEN), `related_reference`, `finding`, `resolution`, `checked_by`,
`description`.

---

## 7. Referential-integrity rules

| Relationship kind | ON DELETE |
|-------------------|-----------|
| Class B row → `projects` | RESTRICT |
| Class B row → catalog table (merge FK) | RESTRICT |
| Parent within a project (`panel_id`, `control_panel_id`, termination `cable_id`) | RESTRICT |
| Self-references (`fed_from_id`, `parent_location_id`) | SET NULL |
| Other optional cross-references | SET NULL |

SQLite is opened with `PRAGMA foreign_keys=ON`; PostgreSQL enforces FKs
natively.

---

## 8. API surface

Every table exposes, under `/api/{table}`: list (pagination + `project_id`
filter + `search` + `sort`/`order`), get, create, update, delete, plus
`/export-csv` and `/import-csv`. The five catalog-linked tables also expose
`/merged` (rows with the catalog record joined in).

Project-scoped composite endpoints: `/api/projects/{id}/dashboard` (row counts)
and `/api/projects/{id}/all` (every Class B row, catalog-merged).
