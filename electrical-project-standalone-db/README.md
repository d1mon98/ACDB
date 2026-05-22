# Electrical Project Standalone DB

A standalone application for building and verifying a database that fully and
accurately reflects an industrial electrical power-distribution and
instrumentation-&-control (I&C) project.

It has a **Python / FastAPI backend** over a local **SQLite** database and a
**React + Vite + TypeScript web UI**. Everything runs locally on one machine;
there is no cloud, no external service and no authentication.

> **Stage 1 scope.** This is the data-model stage: create, populate and verify
> the project database through a web UI. Drawing generation, reporting and
> AutoCAD integration are explicitly out of scope.

---

## The core idea: two classes of tables

Every table is presented in the UI as a **chapter**, and belongs to one of two
classes:

- **Class A — General Catalogs.** Permanent, reusable reference data:
  manufacturers, standard equipment models, standard cable types, instrument
  models, I/O modules, control devices. Seeded once, reused by every project.

- **Class B — Project Tables.** The actual equipment, tags, locations and
  connections of one specific project. Every row carries a `project_id`.

### The Merge Principle

A Class B row is created by **merging a catalog record (permanent data) with
project-specific data (tags, locations, references, settings)**. The merge is a
**foreign key** from the project row to the catalog row — never a copy of the
catalog's fields. The catalog stays the single source of truth.

A Class B row may also be a **custom / one-off item** with no catalog link: the
catalog FK is left null and the permanent attributes are entered directly into
the row's `local_*` columns. A database CHECK constraint guarantees every row
has *either* a catalog reference *or* its custom details.

See [`docs/schema.md`](docs/schema.md) for the full table-by-table reference.

---

## Databases & the Database Browser

Each database is a single SQLite file. Managed databases live in
`backend/databases/`, but a database file anywhere on disk can also be opened.
The **Database Browser** (the first item in the sidebar) is the connection
manager:

- **Connect / Disconnect** — choose which database the application is working
  with. Only one is connected at a time; while none is connected the catalog
  and project chapters are unavailable.
- **Open from File System…** — a file picker to browse the filesystem and open
  a database file from any folder or drive. The file must be an Electrical
  Project Standalone DB database (it is validated on open).
- **Create** — make a new, empty database in the project folder. The full
  schema is applied automatically, so it is ready to use immediately.
- **Rename** — rename a managed database file.
- **Delete** — permanently remove a managed database file (disconnect first).
- **Recent databases** — recently opened databases (including external files)
  are listed for one-click reconnection.

The app reconnects to the last-used database automatically on startup. The
standard setup below creates the first database, `project.db`.

---

## Modules & table tools

The sidebar groups every table into **General Catalogs** (Class A) and
**Project Tables** (Class B). The project tables cover a full electrical / I&C
deliverable set:

> Projects · Locations / Areas · Power Distribution · Equipment ·
> Control Panels · Panel Components · Panel Circuits · Cables · Cable Routes ·
> Conduits / Trays · Instruments · I/O List · Terminal Blocks · Terminations ·
> Network Devices · Drawings · Calculations · QA/QC Checks

Every table grid supports the same actions:

- **Add / Edit / Delete** a row (Delete asks for confirmation).
- **Duplicate** — opens the form pre-filled from a row as a new record; change
  the tag and save.
- **Search** — the search box filters rows across all text columns.
- **Sort** — click any column header to sort; click again to reverse.
- **Export CSV** — downloads the current table (respecting the search filter).
- **Import CSV** — creates rows from a CSV file or pasted text. Column headers
  must match the field names — export first to get a template. Each row is
  validated; a per-row error report is shown for anything rejected.

See [`docs/schema.md`](docs/schema.md) for every table's fields.

---

## Prerequisites

- **Python 3.11+** (developed on 3.14)
- **Node.js 18+** (developed on Node 24 LTS)

## Project layout

```
electrical-project-standalone-db/
  backend/        FastAPI app, SQLAlchemy models, Alembic migrations, seed script
  frontend/       React + Vite + TypeScript web UI
  docs/           schema.md — full schema reference
  README.md       this file
```

---

## Backend — install & run

All commands are run from the `backend/` directory. Examples use Windows
PowerShell; on macOS/Linux use `source .venv/bin/activate` instead.

```powershell
cd backend

# 1. create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. install dependencies
pip install -r requirements.txt

# 3. create the database schema (runs the Alembic migration)
alembic upgrade head

# 4. load generic placeholder data (catalogs + one example project)
python seed.py

# 5. start the API server
uvicorn app.main:app --reload
```

The API is now at **http://127.0.0.1:8000**; interactive API docs are at
**http://127.0.0.1:8000/docs**.

### Migrations

The schema is versioned with Alembic from day one.

```powershell
alembic upgrade head                       # apply all migrations
alembic revision --autogenerate -m "..."   # create a new migration after a model change
alembic downgrade -1                       # roll back one migration
```

### Seed script

```powershell
python seed.py            # seed only if the database is empty
python seed.py --reset    # wipe ALL data, then reseed
```

All seed data is generic placeholder data — no real client, project or vendor
names.

---

## Frontend — install & run

All commands are run from the `frontend/` directory.

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The dev server proxies every `/api` request to
the backend on port 8000, so **the backend must be running** as well.

To produce a static build instead:

```powershell
npm run build      # outputs frontend/dist/
```

If `frontend/dist/` exists, the backend serves it at its root, so
`http://127.0.0.1:8000` then hosts the whole application from a single process.

---

## First walkthrough

With the backend and frontend both running, open **http://localhost:5173**.
The **Database Browser** (top of the sidebar) shows the connected database — the
app auto-connects to `project.db`. From there you can create, rename, switch
between or delete databases. With a database connected:

1. **Create a project.** Open the **Projects** chapter (under *Project Tables*),
   click **+ Add**, fill in a project number and name, and save. Select it in
   the **Active project** dropdown in the header.

2. **Add a catalog item.** Open **Equipment** under *General Catalogs* and add a
   transformer or panelboard — this is permanent, reusable reference data.

3. **Create a merged project row.** Open **Equipment** under *Project Tables*.
   Click **+ Add**: with *From catalog* selected, pick the catalog item you just
   created — its permanent attributes appear read-only. Fill in the
   project-specific fields (equipment tag, location) and save. You have merged a
   catalog record with project data.

4. **Try a custom one-off.** Add another project equipment row, but switch the
   toggle to *Custom item (no catalog)* and type the permanent attributes
   directly. This is the non-standard-item path.

5. **Check the dashboard.** Open **Dashboard** to see a live count per Class B
   chapter — how completely the database reflects the project.

---

## API overview

Every table has a full REST surface under `/api`:

| Method | Path | Purpose |
|--------|------|---------|
| `GET`    | `/api/{table}` | list (`skip`, `limit`, `project_id`, `search`, `sort`, `order`) |
| `GET`    | `/api/{table}/{id}` | get one |
| `POST`   | `/api/{table}` | create |
| `PUT`    | `/api/{table}/{id}` | update (partial) |
| `DELETE` | `/api/{table}/{id}` | delete |
| `GET`    | `/api/{table}/export-csv` | download the table as CSV |
| `POST`   | `/api/{table}/import-csv` | create rows from CSV text |
| `GET`    | `/api/{table}/merged` | Class B catalog-linked: rows with catalog joined |
| `GET`    | `/api/projects/{id}/dashboard` | row counts per Class B chapter |
| `GET`    | `/api/projects/{id}/all` | every Class B row for a project, catalog-merged |

`DELETE /api/projects/{id}` is refused while the project still has dependent
records; pass `?cascade=true` to delete them too.

Database Browser endpoints (these work with no database connected):

| Method | Path | Purpose |
|--------|------|---------|
| `GET`    | `/api/databases` | list all database files + connection status |
| `GET`    | `/api/databases/status` | current connection status |
| `POST`   | `/api/databases` | create a new database (schema applied) |
| `PUT`    | `/api/databases/{name}` | rename a database |
| `DELETE` | `/api/databases/{name}` | delete a database (must be disconnected) |
| `POST`   | `/api/databases/{name}/connect` | connect to a managed database |
| `POST`   | `/api/databases/open` | open a database file by filesystem path |
| `POST`   | `/api/databases/disconnect` | disconnect |
| `GET`    | `/api/fs/browse` | list folders and database files for the file picker |
