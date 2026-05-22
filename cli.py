"""
Electrical Project Database — Click CLI.

Entry point:  python cli.py <command> [options]

Command groups:
  db init           Create a new project
  db add equipment  Add equipment from catalog
  db add cable      Add a cable (FROM-TO)
  db list equipment List equipment for a project
  db list cables    List cables, optionally filtered by FROM tag
  db export cables  Export cable schedule to CSV / JSON / Excel
  db report panel-schedule  Print panel schedule for a panel tag
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import joinedload

from models import (
    Cable,
    CableCatalog,
    CableStatus,
    Equipment,
    EquipCatalog,
    EquipStatus,
    Instrument,
    Location,
    PanelSchedule,
    Phase,
    Project,
    Session,
    VoltageSystem,
    init_db,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_project(session, project_number: str) -> Project:
    proj = session.query(Project).filter_by(project_number=project_number.upper()).first()
    if not proj:
        console.print(f"[red]Project '{project_number}' not found.[/red]")
        sys.exit(1)
    return proj


def _pick_from_catalog(session, model, label: str):
    """Interactive catalog picker — list rows and ask user to choose one."""
    rows = session.query(model).all()
    if not rows:
        console.print(f"[yellow]No entries in {label} catalog. Run seed_catalogs.py first.[/yellow]")
        sys.exit(1)
    table = Table(title=f"{label} Catalog")
    cols = [c.key for c in model.__table__.columns]
    for c in cols:
        table.add_column(c)
    for r in rows:
        table.add_row(*[str(getattr(r, c) or "") for c in cols])
    console.print(table)
    pk_col = list(model.__table__.primary_key.columns)[0].key
    choice = click.prompt(f"Enter {pk_col} to select")
    row = session.query(model).get(int(choice))
    if not row:
        console.print("[red]Invalid selection.[/red]")
        sys.exit(1)
    return row


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------

@click.group()
def db():
    """Electrical Project Database CLI."""
    pass


# ---------------------------------------------------------------------------
# db init
# ---------------------------------------------------------------------------

@db.command("init")
@click.option("--project", "project_number", required=True, help="Project number (e.g. PRJ-001)")
@click.option("--name", "project_name", required=True, help="Project name")
@click.option("--client", default="", help="Client name")
@click.option("--location", default="", help="Project location")
@click.option("--engineer", default="", help="Engineer of record")
@click.option("--nec-edition", default="2023", show_default=True, help="NEC edition year")
@click.option(
    "--voltage-system",
    type=click.Choice([v.value for v in VoltageSystem]),
    default=VoltageSystem.V480Y277.value,
    show_default=True,
)
@click.option("--notes", default="")
def db_init(project_number, project_name, client, location, engineer, nec_edition, voltage_system, notes):
    """Create a new project record and initialize the database."""
    init_db()
    with Session() as session:
        existing = session.query(Project).filter_by(project_number=project_number.upper()).first()
        if existing:
            console.print(f"[yellow]Project {project_number} already exists (id={existing.project_id}).[/yellow]")
            return
        proj = Project(
            project_number=project_number.upper(),
            project_name=project_name,
            client=client,
            location=location,
            engineer_of_record=engineer,
            issue_date=date.today(),
            nec_edition=nec_edition,
            voltage_system=VoltageSystem(voltage_system),
            notes=notes,
        )
        session.add(proj)
        session.commit()
        console.print(f"[green]Project {proj.project_number} created (id={proj.project_id}).[/green]")


# ---------------------------------------------------------------------------
# db add
# ---------------------------------------------------------------------------

@db.group("add")
def db_add():
    """Add records to a project."""
    pass


@db_add.command("equipment")
@click.option("--project", "project_number", required=True)
@click.option("--tag", required=True, help="Equipment tag (uppercase, dash-separated)")
@click.option("--name", default="", help="Equipment name / description")
@click.option("--bus-voltage", type=int, default=None)
@click.option("--fed-from", default="", help="Upstream equipment tag")
@click.option("--breaker-trip", type=float, default=None)
@click.option("--drawing-ref", default="")
@click.option("--sheet-number", default="")
@click.option("--from-catalog", is_flag=True, default=False, help="Pick from equip_catalog interactively")
@click.option("--catalog-id", type=int, default=None, help="equip_catalog_id (skip interactive picker)")
@click.option("--notes", default="")
def add_equipment(project_number, tag, name, bus_voltage, fed_from, breaker_trip,
                  drawing_ref, sheet_number, from_catalog, catalog_id, notes):
    """Add a piece of equipment to a project."""
    with Session() as session:
        proj = _get_project(session, project_number)
        cat_entry = None
        if from_catalog:
            cat_entry = _pick_from_catalog(session, EquipCatalog, "Equipment")
        elif catalog_id:
            cat_entry = session.get(EquipCatalog, catalog_id)

        equip = Equipment(
            project_id=proj.project_id,
            equip_catalog_id=cat_entry.equip_catalog_id if cat_entry else None,
            tag=tag.upper(),
            name=name or (cat_entry.description if cat_entry else ""),
            bus_voltage_v=bus_voltage,
            fed_from_tag=fed_from.upper() if fed_from else None,
            breaker_trip_a=breaker_trip,
            drawing_ref=drawing_ref,
            sheet_number=sheet_number,
            status=EquipStatus.DESIGN,
            notes=notes,
        )
        session.add(equip)
        session.commit()
        console.print(f"[green]Equipment {equip.tag} added (id={equip.equip_id}).[/green]")


@db_add.command("cable")
@click.option("--project", "project_number", required=True)
@click.option("--tag", required=True, help="Cable tag (e.g. C-001)")
@click.option("--from", "from_spec", required=True, help="FROM endpoint: TAG:TERMINAL or TAG (equip or instr tag)")
@click.option("--to", "to_spec", required=True, help="TO endpoint: TAG:TERMINAL or TAG")
@click.option("--service", default="", help="Service description")
@click.option("--length-ft", type=float, default=None)
@click.option("--from-catalog", is_flag=True, default=False)
@click.option("--catalog-id", type=int, default=None)
@click.option("--drawing-ref", default="")
@click.option("--notes", default="")
def add_cable(project_number, tag, from_spec, to_spec, service, length_ft,
              from_catalog, catalog_id, drawing_ref, notes):
    """Add a cable (FROM-TO) to a project."""

    def parse_spec(spec: str):
        parts = spec.split(":", 1)
        return parts[0].upper(), parts[1] if len(parts) > 1 else ""

    with Session() as session:
        proj = _get_project(session, project_number)

        from_tag, from_terminal = parse_spec(from_spec)
        to_tag, to_terminal = parse_spec(to_spec)

        def resolve(tag):
            equip = session.query(Equipment).filter_by(project_id=proj.project_id, tag=tag).first()
            if equip:
                return ("equipment", equip)
            instr = session.query(Instrument).filter_by(project_id=proj.project_id, tag=tag).first()
            if instr:
                return ("instrument", instr)
            return (None, None)

        from_type, from_obj = resolve(from_tag)
        to_type, to_obj = resolve(to_tag)

        if not from_obj:
            console.print(f"[red]FROM tag '{from_tag}' not found in project {project_number}.[/red]")
            sys.exit(1)
        if not to_obj:
            console.print(f"[red]TO tag '{to_tag}' not found in project {project_number}.[/red]")
            sys.exit(1)

        cat_entry = None
        if from_catalog:
            cat_entry = _pick_from_catalog(session, CableCatalog, "Cable")
        elif catalog_id:
            cat_entry = session.get(CableCatalog, catalog_id)

        cable = Cable(
            project_id=proj.project_id,
            cable_catalog_id=cat_entry.cable_catalog_id if cat_entry else None,
            cable_tag=tag.upper(),
            service_description=service,
            from_equipment_id=from_obj.equip_id if from_type == "equipment" else None,
            from_instrument_id=from_obj.instrument_id if from_type == "instrument" else None,
            from_terminal=from_terminal,
            to_equipment_id=to_obj.equip_id if to_type == "equipment" else None,
            to_instrument_id=to_obj.instrument_id if to_type == "instrument" else None,
            to_terminal=to_terminal,
            length_ft=length_ft,
            drawing_ref=drawing_ref,
            status=CableStatus.DESIGN,
            notes=notes,
        )
        session.add(cable)
        session.commit()
        console.print(f"[green]Cable {cable.cable_tag} added (id={cable.cable_id}): {from_tag} -> {to_tag}.[/green]")


# ---------------------------------------------------------------------------
# db list
# ---------------------------------------------------------------------------

@db.group("list")
def db_list():
    """List records in a project."""
    pass


@db_list.command("equipment")
@click.option("--project", "project_number", required=True)
@click.option("--status", default=None, help="Filter by status")
def list_equipment(project_number, status):
    """List equipment register for a project."""
    with Session() as session:
        proj = _get_project(session, project_number)
        q = session.query(Equipment).filter_by(project_id=proj.project_id)
        if status:
            q = q.filter(Equipment.status == status.upper())
        rows = q.order_by(Equipment.tag).all()

        table = Table(title=f"Equipment — {proj.project_number}: {proj.project_name}")
        for col in ("Tag", "Name", "Voltage (V)", "Fed From", "Breaker (A)", "Drawing", "Status"):
            table.add_column(col)
        for r in rows:
            table.add_row(
                r.tag,
                r.name or "",
                str(r.bus_voltage_v or ""),
                r.fed_from_tag or "",
                str(r.breaker_trip_a or ""),
                f"{r.drawing_ref or ''} / {r.sheet_number or ''}",
                r.status.value if r.status else "",
            )
        console.print(table)
        console.print(f"[dim]{len(rows)} record(s)[/dim]")


@db_list.command("cables")
@click.option("--project", "project_number", required=True)
@click.option("--from-tag", default=None, help="Filter by FROM equipment/instrument tag")
@click.option("--status", default=None)
def list_cables(project_number, from_tag, status):
    """List cable schedule for a project."""
    with Session() as session:
        proj = _get_project(session, project_number)
        q = (
            session.query(Cable)
            .options(
                joinedload(Cable.from_equipment),
                joinedload(Cable.from_instrument),
                joinedload(Cable.to_equipment),
                joinedload(Cable.to_instrument),
            )
            .filter_by(project_id=proj.project_id)
        )
        if status:
            q = q.filter(Cable.status == status.upper())
        rows = q.order_by(Cable.cable_tag).all()

        if from_tag:
            ftag = from_tag.upper()
            rows = [r for r in rows if r.from_tag == ftag]

        table = Table(title=f"Cable Schedule — {proj.project_number}")
        for col in ("Cable Tag", "Service", "FROM Tag", "FROM Term.", "TO Tag", "TO Term.", "Length (ft)", "Status"):
            table.add_column(col)
        for r in rows:
            table.add_row(
                r.cable_tag,
                r.service_description or "",
                r.from_tag,
                r.from_terminal or "",
                r.to_tag,
                r.to_terminal or "",
                str(r.length_ft or ""),
                r.status.value if r.status else "",
            )
        console.print(table)
        console.print(f"[dim]{len(rows)} record(s)[/dim]")


# ---------------------------------------------------------------------------
# db export
# ---------------------------------------------------------------------------

@db.group("export")
def db_export():
    """Export project data."""
    pass


@db_export.command("cables")
@click.option("--project", "project_number", required=True)
@click.option("--format", "fmt", type=click.Choice(["csv", "json", "excel"]), default="csv", show_default=True)
@click.option("--output", "output_dir", default="./export", show_default=True)
def export_cables(project_number, fmt, output_dir):
    """Export the cable schedule to CSV, JSON, or Excel."""
    with Session() as session:
        proj = _get_project(session, project_number)
        cables = (
            session.query(Cable)
            .options(
                joinedload(Cable.from_equipment),
                joinedload(Cable.from_instrument),
                joinedload(Cable.to_equipment),
                joinedload(Cable.to_instrument),
            )
            .filter_by(project_id=proj.project_id)
            .order_by(Cable.cable_tag)
            .all()
        )

        headers = [
            "cable_tag", "service_description", "from_tag", "from_terminal",
            "to_tag", "to_terminal", "conduit_tag", "length_ft", "length_ft_actual",
            "num_conductors_used", "conductor_size_awg_kcmil", "voltage_drop_pct",
            "drawing_ref", "sheet_number", "status", "notes",
        ]

        def row_dict(c: Cable) -> dict:
            return {
                "cable_tag": c.cable_tag,
                "service_description": c.service_description or "",
                "from_tag": c.from_tag,
                "from_terminal": c.from_terminal or "",
                "to_tag": c.to_tag,
                "to_terminal": c.to_terminal or "",
                "conduit_tag": c.conduit_tag or "",
                "length_ft": c.length_ft,
                "length_ft_actual": c.length_ft_actual,
                "num_conductors_used": c.num_conductors_used,
                "conductor_size_awg_kcmil": c.conductor_size_awg_kcmil or "",
                "voltage_drop_pct": c.voltage_drop_pct,
                "drawing_ref": c.drawing_ref or "",
                "sheet_number": c.sheet_number or "",
                "status": c.status.value if c.status else "",
                "notes": c.notes or "",
            }

        data = [row_dict(c) for c in cables]
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        stem = f"{proj.project_number}_cables"

        if fmt == "csv":
            fpath = out_path / f"{stem}.csv"
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            console.print(f"[green]Exported {len(data)} cables -> {fpath}[/green]")

        elif fmt == "json":
            fpath = out_path / f"{stem}.json"
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            console.print(f"[green]Exported {len(data)} cables -> {fpath}[/green]")

        elif fmt == "excel":
            try:
                import openpyxl
            except ImportError:
                console.print("[red]openpyxl not installed. Run: pip install openpyxl[/red]")
                sys.exit(1)
            fpath = out_path / f"{stem}.xlsx"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Cable Schedule"
            ws.append(headers)
            for d in data:
                ws.append([d.get(h) for h in headers])
            # Auto-width
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)
            wb.save(fpath)
            console.print(f"[green]Exported {len(data)} cables -> {fpath}[/green]")


# ---------------------------------------------------------------------------
# db report
# ---------------------------------------------------------------------------

@db.group("report")
def db_report():
    """Generate reports."""
    pass


@db_report.command("panel-schedule")
@click.option("--project", "project_number", required=True)
@click.option("--panel", "panel_tag", required=True, help="Panel equipment tag")
def report_panel_schedule(project_number, panel_tag):
    """Print the panel schedule for a given panel tag."""
    with Session() as session:
        proj = _get_project(session, project_number)
        panel = session.query(Equipment).filter_by(
            project_id=proj.project_id, tag=panel_tag.upper()
        ).first()
        if not panel:
            console.print(f"[red]Panel '{panel_tag}' not found in project {project_number}.[/red]")
            sys.exit(1)

        schedules = (
            session.query(PanelSchedule)
            .filter_by(panel_equip_id=panel.equip_id)
            .options(
                joinedload(PanelSchedule.load_equip),
                joinedload(PanelSchedule.load_instrument),
            )
            .order_by(PanelSchedule.circuit_number)
            .all()
        )

        total_kva = sum(s.load_kva or 0 for s in schedules)
        total_kw = sum(s.load_kw or 0 for s in schedules)

        table = Table(title=f"Panel Schedule — {panel.tag} ({proj.project_number})")
        for col in ("Ckt #", "Phase", "Trip (A)", "Poles", "Load Tag", "Description", "kVA", "kW", "PF", "Notes"):
            table.add_column(col)

        for s in schedules:
            load_tag = ""
            if s.load_equip:
                load_tag = s.load_equip.tag
            elif s.load_instrument:
                load_tag = s.load_instrument.tag

            table.add_row(
                s.circuit_number,
                s.phase.value if s.phase else "",
                str(s.breaker_trip_a or ""),
                str(s.breaker_poles or ""),
                load_tag,
                s.load_description or "",
                f"{s.load_kva:.1f}" if s.load_kva else "",
                f"{s.load_kw:.1f}" if s.load_kw else "",
                f"{s.load_pf:.2f}" if s.load_pf else "",
                s.notes or "",
            )

        console.print(table)
        console.print(f"[bold]Total connected: {total_kva:.1f} kVA  /  {total_kw:.1f} kW[/bold]")
        console.print(f"[dim]{len(schedules)} circuit(s)[/dim]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db()
