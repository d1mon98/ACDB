# AutoCAD_Database_Plugin — Electrical Project Database

Local SQLite database for industrial and commercial electrical and control projects (US / NEC).
Python CLI for all operations. Future-ready hook for AutoCAD Sheet Set integration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLASS A — GLOBAL CATALOGS                    │
│   (permanent, shared across all projects — seeded once)        │
│                                                                 │
│  equip_catalog    cable_catalog    instrument_catalog           │
│  conduit_catalog                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │  FK pull-through (catalog_id)
┌──────────────────────────▼──────────────────────────────────────┐
│                   CLASS B — PROJECT TABLES                      │
│             (per-project, all carry project_id FK)              │
│                                                                 │
│  projects  ──►  locations                                       │
│            ──►  equipment    ◄──── equip_catalog                │
│            ──►  instruments  ◄──── instrument_catalog           │
│            ──►  cables (FROM-TO: equip↔equip, equip↔instr,     │
│                         instr↔instr) ◄── cable_catalog          │
│            ──►  conduits     ◄──── conduit_catalog              │
│            ──►  panel_schedules ──► equipment (panel)           │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              sheetset_sync.py  (STUB — future)                  │
│   Reads AutoCAD .dst XML → maps sheets to drawing_ref /        │
│   sheet_number in all Class B tables                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Layout

```
ACDB/
├── models.py           SQLAlchemy ORM — all CLASS A and CLASS B tables
├── cli.py              Click CLI entry point
├── seed_catalogs.py    Seeds CLASS A catalogs with 5-10 generic entries
├── sheetset_sync.py    AutoCAD Sheet Set sync stub (not yet active)
├── requirements.txt
├── alembic.ini
└── alembic/
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 0001_initial_schema.py
```

---

## Setup

```bash
cd "path\to\ACDB"
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Apply migrations (creates acdb.db)
alembic upgrade head

# Seed CLASS A catalogs
python seed_catalogs.py
```

Set `ACDB_URL` environment variable to override the default `sqlite:///acdb.db`:

```powershell
$env:ACDB_URL = "sqlite:///C:/projects/myproject.db"
```

---

## CLI Usage

All commands are accessed via `python cli.py <command>`.
(`db` in the spec maps to `python cli.py` — it is the root command group.)

### Create a project

```bash
python cli.py init \
  --project PRJ-001 \
  --name "Water Treatment Facility Expansion" \
  --client "City of Springfield" \
  --location "Springfield, IL" \
  --engineer "J. Smith, PE" \
  --nec-edition 2023 \
  --voltage-system 480Y/277
```

### Add equipment (from catalog interactively)

```bash
python cli.py add equipment \
  --project PRJ-001 \
  --tag MCC-1A \
  --bus-voltage 480 \
  --fed-from SWGR-1 \
  --breaker-trip 800 \
  --from-catalog
```

### Add a cable (FROM -> TO)

Endpoint format: `TAG` or `TAG:TERMINAL`

```bash
python cli.py add cable \
  --project PRJ-001 \
  --tag C-001 \
  --from "MCC-1A:L1" \
  --to "PUMP-1:T1" \
  --service "480V PUMP FEED" \
  --length-ft 220
```

### List equipment

```bash
python cli.py list equipment --project PRJ-001
python cli.py list equipment --project PRJ-001 --status DESIGN
```

### List cables (optional FROM-tag filter)

```bash
python cli.py list cables --project PRJ-001
python cli.py list cables --project PRJ-001 --from-tag MCC-1A
```

### Export cable schedule

```bash
python cli.py export cables --project PRJ-001 --format csv    --output ./export/
python cli.py export cables --project PRJ-001 --format json   --output ./export/
python cli.py export cables --project PRJ-001 --format excel  --output ./export/
```

### Panel schedule report

```bash
python cli.py report panel-schedule --project PRJ-001 --panel PANEL-A
```

---

## NEC Design Rules Implemented

| Rule | NEC Reference | Location |
|------|--------------|----------|
| Voltage drop (single-phase) | NEC 210.19, 215.2 | `Cable.calc_voltage_drop()` |
| Voltage drop (three-phase)  | NEC 210.19, 215.2 | `Cable.calc_voltage_drop()` |

Formula:
- Single-phase: `vd_pct = (2 × L × I × R) / (1000 × V) × 100`
- Three-phase:  `vd_pct = (1.732 × L × I × R) / (1000 × V) × 100`

---

## Migrations

Generate a new migration after changing `models.py`:

```bash
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

Roll back one step:

```bash
alembic downgrade -1
```

---

## AutoCAD Sheet Set Hook (Future)

`sheetset_sync.py` is a documented stub. When activated it will:

1. Parse an AutoCAD `.dst` XML file.
2. Diff sheet numbers against `drawing_ref` / `sheet_number` fields in all Class B tables.
3. Upsert a `sheet_metadata` table (to be added in a future migration).

To activate: implement `parse_dst()` and `sync_to_db()` in `sheetset_sync.py`, add the
`sheet_metadata` table to `models.py`, run `alembic revision --autogenerate`, and wire up
`python cli.py db sync sheetset --dst <path> --project <PRJ>`.
