// Slide-in properties panel shown when a relationship edge is selected.
// Handles both FK-derived edges (read-only) and user-defined relationships (editable).

import { useEffect, useState } from "react";
import { api } from "../api";
import type {
  CascadeOp,
  ErdEdgeData,
  ErdRelationship,
  RelType,
} from "../types";

const REL_TYPES: RelType[] = ["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_MANY"];
const CASCADE_OPS: CascadeOp[] = [
  "NO ACTION",
  "RESTRICT",
  "SET NULL",
  "SET DEFAULT",
  "CASCADE",
];

interface Props {
  edgeId: string | null;
  edgeData: ErdEdgeData | null;
  sourceTable: string;
  targetTable: string;
  onClose: () => void;
  onDeleted: (relId: number) => void;
  onUpdated: (rel: ErdRelationship) => void;
}

export default function RelationshipPanel({
  edgeId,
  edgeData,
  sourceTable,
  targetTable,
  onClose,
  onDeleted,
  onUpdated,
}: Props) {
  const isFk = edgeData?.source === "fk";

  const [form, setForm] = useState<Partial<ErdRelationship>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Populate form when a new edge is selected.
  useEffect(() => {
    if (!edgeData) return;
    setForm({
      parent_table:   sourceTable,
      child_table:    targetTable,
      foreign_key:    edgeData.from_col ?? (edgeData.foreign_key as string | undefined) ?? null,
      rel_type:       edgeData.rel_type ?? "ONE_TO_MANY",
      cascade_update: (edgeData.cascade_update as CascadeOp) ?? "NO ACTION",
      cascade_delete: (edgeData.cascade_delete as CascadeOp) ?? "NO ACTION",
      label:          edgeData.label ?? null,
      notes:          null,
      id:             edgeData.rel_id,
    });
    setError(null);
  }, [edgeId, edgeData, sourceTable, targetTable]);

  function field(key: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [key]: value || null }));
  }

  async function handleSave() {
    if (isFk || !form.id) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.erd.updateRelationship(form.id, {
        parent_table:   form.parent_table,
        child_table:    form.child_table,
        foreign_key:    form.foreign_key ?? undefined,
        rel_type:       form.rel_type as RelType,
        cascade_update: form.cascade_update as CascadeOp,
        cascade_delete: form.cascade_delete as CascadeOp,
        label:          form.label ?? undefined,
        notes:          form.notes ?? undefined,
      });
      onUpdated(updated);
    } catch (e: any) {
      setError(e?.message ?? "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (isFk || !form.id) return;
    if (!confirm("Delete this relationship?")) return;
    try {
      await api.erd.deleteRelationship(form.id);
      onDeleted(form.id);
    } catch (e: any) {
      setError(e?.message ?? "Delete failed.");
    }
  }

  if (!edgeData) return null;

  return (
    <div className="erd-panel">
      <div className="erd-panel__header">
        <span className="erd-panel__title">
          {isFk ? "Foreign Key Relationship" : "Relationship Properties"}
        </span>
        <button className="erd-panel__close" onClick={onClose} title="Close">✕</button>
      </div>

      {isFk && (
        <div className="erd-panel__badge">Derived from schema — read only</div>
      )}

      <div className="erd-panel__body">
        <label className="erd-panel__label">Parent (source) table
          <input className="erd-panel__input" value={form.parent_table ?? ""} disabled={isFk}
            onChange={(e) => field("parent_table", e.target.value)} />
        </label>

        <label className="erd-panel__label">Child (target) table
          <input className="erd-panel__input" value={form.child_table ?? ""} disabled={isFk}
            onChange={(e) => field("child_table", e.target.value)} />
        </label>

        <label className="erd-panel__label">Foreign key column
          <input className="erd-panel__input" value={form.foreign_key ?? ""} disabled={isFk}
            onChange={(e) => field("foreign_key", e.target.value)} />
        </label>

        <label className="erd-panel__label">Relationship type
          <select className="erd-panel__input" value={form.rel_type ?? "ONE_TO_MANY"} disabled={isFk}
            onChange={(e) => field("rel_type", e.target.value)}>
            {REL_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </label>

        <label className="erd-panel__label">On update
          <select className="erd-panel__input" value={form.cascade_update ?? "NO ACTION"} disabled={isFk}
            onChange={(e) => field("cascade_update", e.target.value)}>
            {CASCADE_OPS.map((o) => <option key={o}>{o}</option>)}
          </select>
        </label>

        <label className="erd-panel__label">On delete
          <select className="erd-panel__input" value={form.cascade_delete ?? "NO ACTION"} disabled={isFk}
            onChange={(e) => field("cascade_delete", e.target.value)}>
            {CASCADE_OPS.map((o) => <option key={o}>{o}</option>)}
          </select>
        </label>

        {!isFk && (
          <>
            <label className="erd-panel__label">Label
              <input className="erd-panel__input" value={form.label ?? ""}
                onChange={(e) => field("label", e.target.value)} />
            </label>
            <label className="erd-panel__label">Notes
              <textarea className="erd-panel__input erd-panel__textarea" value={form.notes ?? ""}
                onChange={(e) => field("notes", e.target.value)} />
            </label>
          </>
        )}

        {isFk && edgeData.from_col && (
          <div className="erd-panel__info">
            <span>Column</span>
            <code>{edgeData.from_col} → {edgeData.to_col}</code>
          </div>
        )}
      </div>

      {error && <div className="form-error" style={{ margin: "0 12px 8px" }}>{error}</div>}

      {!isFk && (
        <div className="erd-panel__footer">
          <button className="btn btn-danger" onClick={handleDelete}>Delete</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      )}
    </div>
  );
}
