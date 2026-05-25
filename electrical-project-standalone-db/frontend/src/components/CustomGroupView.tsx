// Two-tab view for a user-created catalog group:
//   Structure tab -- define/edit/delete columns
//   Data tab      -- add/edit/delete rows using those columns

import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { ColumnDef, ColumnDefCreate, CustomColType, CustomRow } from "../types";

const COL_TYPES: { value: CustomColType; label: string }[] = [
  { value: "text",     label: "Text" },
  { value: "number",   label: "Number" },
  { value: "bool",     label: "Boolean" },
  { value: "textarea", label: "Long text" },
];

// ---------------------------------------------------------------------------
// Structure tab
// ---------------------------------------------------------------------------

function StructureTab({ groupId }: { groupId: number }) {
  const [cols, setCols]         = useState<ColumnDef[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [editId, setEditId]     = useState<number | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editType, setEditType]   = useState<CustomColType>("text");
  const [editRequired, setEditRequired] = useState(false);
  const [editOrder, setEditOrder] = useState(0);

  // add-column form state
  const [showAdd, setShowAdd]   = useState(false);
  const [newName, setNewName]   = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [newType, setNewType]   = useState<CustomColType>("text");
  const [newRequired, setNewRequired] = useState(false);
  const [newOrder, setNewOrder] = useState(0);
  const [adding, setAdding]     = useState(false);

  function loadCols() {
    setLoading(true);
    api.customTable.listColumns(groupId)
      .then(setCols)
      .catch((e) => setError(e?.message ?? "Load failed."))
      .finally(() => setLoading(false));
  }
  useEffect(loadCols, [groupId]);

  function slugify(label: string) {
    return label.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
  }

  async function handleAdd() {
    if (!newName.trim() || !newLabel.trim()) return;
    setAdding(true);
    try {
      const body: ColumnDefCreate = {
        col_name: newName.trim(),
        col_label: newLabel.trim(),
        col_type: newType,
        required: newRequired,
        display_order: newOrder,
      };
      const created = await api.customTable.createColumn(groupId, body);
      setCols((prev) => [...prev, created].sort((a, b) => a.display_order - b.display_order || a.id - b.id));
      setShowAdd(false);
      setNewName(""); setNewLabel(""); setNewType("text"); setNewRequired(false); setNewOrder(0);
    } catch (e: any) {
      setError(e?.message ?? "Add failed.");
    } finally {
      setAdding(false);
    }
  }

  async function handleSaveEdit(col: ColumnDef) {
    try {
      const updated = await api.customTable.updateColumn(groupId, col.id, {
        col_label: editLabel,
        col_type: editType,
        required: editRequired,
        display_order: editOrder,
      });
      setCols((prev) => prev.map((c) => (c.id === col.id ? updated : c)));
      setEditId(null);
    } catch (e: any) {
      setError(e?.message ?? "Save failed.");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this column? All row data for this column will be lost.")) return;
    try {
      await api.customTable.deleteColumn(groupId, id);
      setCols((prev) => prev.filter((c) => c.id !== id));
    } catch (e: any) {
      setError(e?.message ?? "Delete failed.");
    }
  }

  if (loading) return <div className="cg-loading">Loading columns…</div>;

  return (
    <div className="cg-section">
      {error && <div className="form-error" style={{ marginBottom: 10 }}>{error}</div>}

      <table className="cg-table">
        <thead>
          <tr>
            <th>Col name (key)</th>
            <th>Label</th>
            <th>Type</th>
            <th>Required</th>
            <th>Order</th>
            <th style={{ width: 90 }}></th>
          </tr>
        </thead>
        <tbody>
          {cols.length === 0 && (
            <tr><td colSpan={6} style={{ textAlign: "center", color: "#888" }}>No columns yet. Add one below.</td></tr>
          )}
          {cols.map((col) =>
            editId === col.id ? (
              <tr key={col.id} className="cg-edit-row">
                <td><code>{col.col_name}</code></td>
                <td>
                  <input className="cg-input" value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)} />
                </td>
                <td>
                  <select className="cg-input" value={editType}
                    onChange={(e) => setEditType(e.target.value as CustomColType)}>
                    {COL_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </td>
                <td style={{ textAlign: "center" }}>
                  <input type="checkbox" checked={editRequired}
                    onChange={(e) => setEditRequired(e.target.checked)} />
                </td>
                <td>
                  <input className="cg-input" type="number" value={editOrder}
                    onChange={(e) => setEditOrder(Number(e.target.value))}
                    style={{ width: 50 }} />
                </td>
                <td>
                  <button className="btn btn-primary btn-xs" onClick={() => handleSaveEdit(col)}>Save</button>{" "}
                  <button className="btn btn-xs" onClick={() => setEditId(null)}>Cancel</button>
                </td>
              </tr>
            ) : (
              <tr key={col.id}>
                <td><code>{col.col_name}</code></td>
                <td>{col.col_label}</td>
                <td>{col.col_type}</td>
                <td style={{ textAlign: "center" }}>{col.required ? "✓" : "—"}</td>
                <td>{col.display_order}</td>
                <td>
                  <button className="btn btn-xs" onClick={() => {
                    setEditId(col.id); setEditLabel(col.col_label);
                    setEditType(col.col_type); setEditRequired(col.required);
                    setEditOrder(col.display_order);
                  }}>Edit</button>{" "}
                  <button className="btn btn-danger btn-xs" onClick={() => handleDelete(col.id)}>✕</button>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>

      {showAdd ? (
        <div className="cg-add-form">
          <div className="cg-add-grid">
            <label>
              Label
              <input className="cg-input" placeholder="e.g. Voltage Rating"
                value={newLabel}
                onChange={(e) => {
                  setNewLabel(e.target.value);
                  setNewName(slugify(e.target.value));
                }} />
            </label>
            <label>
              Key (auto)
              <input className="cg-input" placeholder="e.g. voltage_rating"
                value={newName}
                onChange={(e) => setNewName(e.target.value)} />
            </label>
            <label>
              Type
              <select className="cg-input" value={newType}
                onChange={(e) => setNewType(e.target.value as CustomColType)}>
                {COL_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={newRequired}
                onChange={(e) => setNewRequired(e.target.checked)} />
              Required
            </label>
            <label>
              Order
              <input className="cg-input" type="number" value={newOrder}
                onChange={(e) => setNewOrder(Number(e.target.value))}
                style={{ width: 60 }} />
            </label>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button className="btn btn-primary" onClick={handleAdd}
              disabled={adding || !newName.trim() || !newLabel.trim()}>
              {adding ? "Adding…" : "Add column"}
            </button>
            <button className="btn" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button className="btn btn-primary" style={{ marginTop: 12 }}
          onClick={() => setShowAdd(true)}>
          + Add column
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data tab
// ---------------------------------------------------------------------------

function DataTab({ groupId }: { groupId: number }) {
  const [cols, setCols]       = useState<ColumnDef[]>([]);
  const [rows, setRows]       = useState<CustomRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [editId, setEditId]   = useState<number | null>(null);
  const [editData, setEditData] = useState<Record<string, unknown>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newData, setNewData] = useState<Record<string, unknown>>({});
  const [adding, setAdding]   = useState(false);

  function load() {
    setLoading(true);
    Promise.all([
      api.customTable.listColumns(groupId),
      api.customTable.listRows(groupId),
    ]).then(([c, r]) => { setCols(c); setRows(r); })
      .catch((e) => setError(e?.message ?? "Load failed."))
      .finally(() => setLoading(false));
  }
  useEffect(load, [groupId]);

  function emptyValues() {
    return Object.fromEntries(cols.map((c) => [c.col_name, c.col_type === "bool" ? false : ""]));
  }

  function fieldInput(
    col: ColumnDef,
    value: unknown,
    onChange: (v: unknown) => void,
  ) {
    const strVal = value === null || value === undefined ? "" : String(value);
    if (col.col_type === "bool") {
      return (
        <input type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)} />
      );
    }
    if (col.col_type === "number") {
      return (
        <input className="cg-input" type="number" value={strVal}
          onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))} />
      );
    }
    if (col.col_type === "textarea") {
      return (
        <textarea className="cg-input" value={strVal}
          onChange={(e) => onChange(e.target.value)}
          rows={2} style={{ resize: "vertical" }} />
      );
    }
    return (
      <input className="cg-input" type="text" value={strVal}
        onChange={(e) => onChange(e.target.value)} />
    );
  }

  async function handleAdd() {
    setAdding(true);
    try {
      const created = await api.customTable.createRow(groupId, newData);
      setRows((prev) => [...prev, created]);
      setShowAdd(false);
      setNewData({});
    } catch (e: any) {
      setError(e?.message ?? "Add failed.");
    } finally {
      setAdding(false);
    }
  }

  async function handleSaveEdit(row: CustomRow) {
    try {
      const updated = await api.customTable.updateRow(groupId, row.id, editData);
      setRows((prev) => prev.map((r) => (r.id === row.id ? updated : r)));
      setEditId(null);
    } catch (e: any) {
      setError(e?.message ?? "Save failed.");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this row?")) return;
    try {
      await api.customTable.deleteRow(groupId, id);
      setRows((prev) => prev.filter((r) => r.id !== id));
    } catch (e: any) {
      setError(e?.message ?? "Delete failed.");
    }
  }

  if (loading) return <div className="cg-loading">Loading data…</div>;

  if (cols.length === 0) {
    return (
      <div className="cg-empty">
        No columns defined yet. Go to the <strong>Structure</strong> tab to add columns first.
      </div>
    );
  }

  return (
    <div className="cg-section">
      {error && <div className="form-error" style={{ marginBottom: 10 }}>{error}</div>}

      <div style={{ overflowX: "auto" }}>
        <table className="cg-table">
          <thead>
            <tr>
              {cols.map((c) => <th key={c.id}>{c.col_label}</th>)}
              <th style={{ width: 90 }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={cols.length + 1} style={{ textAlign: "center", color: "#888" }}>No data yet.</td></tr>
            )}
            {rows.map((row) =>
              editId === row.id ? (
                <tr key={row.id} className="cg-edit-row">
                  {cols.map((col) => (
                    <td key={col.id}>
                      {fieldInput(col, editData[col.col_name], (v) =>
                        setEditData((prev) => ({ ...prev, [col.col_name]: v }))
                      )}
                    </td>
                  ))}
                  <td>
                    <button className="btn btn-primary btn-xs" onClick={() => handleSaveEdit(row)}>Save</button>{" "}
                    <button className="btn btn-xs" onClick={() => setEditId(null)}>Cancel</button>
                  </td>
                </tr>
              ) : (
                <tr key={row.id}>
                  {cols.map((col) => (
                    <td key={col.id}>
                      {col.col_type === "bool"
                        ? (row.row_data[col.col_name] ? "✓" : "—")
                        : String(row.row_data[col.col_name] ?? "")}
                    </td>
                  ))}
                  <td>
                    <button className="btn btn-xs" onClick={() => {
                      setEditId(row.id);
                      setEditData({ ...emptyValues(), ...row.row_data });
                    }}>Edit</button>{" "}
                    <button className="btn btn-danger btn-xs" onClick={() => handleDelete(row.id)}>✕</button>
                  </td>
                </tr>
              )
            )}

            {/* Inline add row */}
            {showAdd && (
              <tr className="cg-edit-row">
                {cols.map((col) => (
                  <td key={col.id}>
                    {fieldInput(col, newData[col.col_name], (v) =>
                      setNewData((prev) => ({ ...prev, [col.col_name]: v }))
                    )}
                  </td>
                ))}
                <td>
                  <button className="btn btn-primary btn-xs" onClick={handleAdd}
                    disabled={adding}>Save</button>{" "}
                  <button className="btn btn-xs" onClick={() => setShowAdd(false)}>Cancel</button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!showAdd && (
        <button className="btn btn-primary" style={{ marginTop: 12 }}
          onClick={() => { setNewData(emptyValues()); setShowAdd(true); }}>
          + Add row
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function CustomGroupView({ groupId }: { groupId: number }) {
  const [tab, setTab] = useState<"structure" | "data">("structure");
  const [groupName, setGroupName] = useState<string>("");

  useEffect(() => {
    api.catalogGroups.get(groupId)
      .then((g) => setGroupName(g.group_name))
      .catch(() => {});
  }, [groupId]);

  return (
    <div className="cg-view">
      <div className="cg-header">
        <h2 className="cg-title">{groupName || "Custom Table"}</h2>
        <div className="cg-tabs">
          <button
            className={"cg-tab" + (tab === "structure" ? " cg-tab--active" : "")}
            onClick={() => setTab("structure")}
          >
            Structure
          </button>
          <button
            className={"cg-tab" + (tab === "data" ? " cg-tab--active" : "")}
            onClick={() => setTab("data")}
          >
            Data
          </button>
        </div>
      </div>

      {tab === "structure"
        ? <StructureTab key={groupId} groupId={groupId} />
        : <DataTab key={groupId} groupId={groupId} />}
    </div>
  );
}
