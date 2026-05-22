// Generic data grid for one chapter.
//
// Columns come from chapter.gridFields.  Foreign-key columns are resolved to a
// readable label using the supplied fkOptions; the special "__source__" column
// shows, for catalog-linked tables, whether a row is merged from the catalog or
// a custom one-off.  Column headers (except the computed "__source__") are
// clickable to sort.

import type { ChapterDef, Row } from "../types";
import { getChapter } from "../chapters";

interface Props {
  chapter: ChapterDef;
  rows: Row[];
  /** chapterKey -> rows of that chapter, used to resolve FK labels. */
  fkOptions: Record<string, Row[]>;
  sort: string | null;
  order: "asc" | "desc";
  onSort: (field: string) => void;
  onEdit: (row: Row) => void;
  onDuplicate: (row: Row) => void;
  onDelete: (row: Row) => void;
}

function fkLabel(fkChapterKey: string, id: unknown, fkOptions: Record<string, Row[]>): string {
  if (id === null || id === undefined) return "—";
  const target = fkOptions[fkChapterKey] ?? [];
  const match = target.find((r) => r.id === id);
  if (!match) return `#${id}`;
  const labelField = getChapter(fkChapterKey).fkLabelField;
  return String(match[labelField] ?? `#${id}`);
}

export default function DataGrid({
  chapter,
  rows,
  fkOptions,
  sort,
  order,
  onSort,
  onEdit,
  onDuplicate,
  onDelete,
}: Props) {
  function headerLabel(gridField: string): string {
    if (gridField === "__source__") return "Catalog / Custom";
    const field = chapter.fields.find((f) => f.name === gridField);
    return field ? field.label : gridField;
  }

  function sortIndicator(gridField: string): string {
    if (sort !== gridField) return "";
    return order === "asc" ? " ▲" : " ▼";
  }

  function renderCell(row: Row, gridField: string) {
    // Merge source column.
    if (gridField === "__source__" && chapter.merge) {
      if (row.is_custom) {
        const localVal = row[chapter.merge.primaryLocalField];
        return (
          <span>
            <span className="badge badge-custom">Custom</span> {localVal ?? "—"}
          </span>
        );
      }
      const catalog: Row | null = row.catalog ?? null;
      const label = catalog
        ? chapter.merge.catalogLabelFields
            .map((f) => catalog[f])
            .filter(Boolean)
            .join(" / ")
        : "—";
      return (
        <span>
          <span className="badge badge-catalog">Catalog</span> {label}
        </span>
      );
    }

    const field = chapter.fields.find((f) => f.name === gridField);
    const value = row[gridField];

    if (field?.type === "fk" && field.fkChapter) {
      return fkLabel(field.fkChapter, value, fkOptions);
    }
    if (field?.type === "bool") {
      return value ? "Yes" : "No";
    }
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    return String(value);
  }

  if (rows.length === 0) {
    return <div className="empty">No records. Use “+ Add” or “Import CSV” to create some.</div>;
  }

  return (
    <div className="grid-wrap">
      <table className="grid">
        <thead>
          <tr>
            <th className="col-id sortable" onClick={() => onSort("id")}>
              ID{sortIndicator("id")}
            </th>
            {chapter.gridFields.map((gf) =>
              gf === "__source__" ? (
                <th key={gf}>{headerLabel(gf)}</th>
              ) : (
                <th key={gf} className="sortable" onClick={() => onSort(gf)}>
                  {headerLabel(gf)}
                  {sortIndicator(gf)}
                </th>
              ),
            )}
            <th className="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td className="col-id">{row.id}</td>
              {chapter.gridFields.map((gf) => (
                <td key={gf}>{renderCell(row, gf)}</td>
              ))}
              <td className="col-actions">
                <button className="btn btn-sm" onClick={() => onEdit(row)}>
                  Edit
                </button>
                <button className="btn btn-sm" onClick={() => onDuplicate(row)}>
                  Duplicate
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => onDelete(row)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
