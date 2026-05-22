// Create / edit form for one record, rendered as a modal.
//
// For the five catalog-linked Class B tables this form implements the merge
// workflow: a toggle chooses between picking a catalog record (its permanent
// fields then show read-only) and entering a custom one-off (the local_*
// permanent fields become editable).

import { useState } from "react";
import { api } from "../api";
import { getChapter } from "../chapters";
import type { ChapterDef, FieldDef, Row } from "../types";
import SearchableSelect from "./SearchableSelect";

interface Props {
  chapter: ChapterDef;
  row: Row | null; // null => creating a new record
  /** When true, `row` is used only as a template -- the save creates a new row. */
  isDuplicate?: boolean;
  fkOptions: Record<string, Row[]>;
  projectId: number | null;
  onClose: () => void;
  onSaved: () => void;
}

type Mode = "catalog" | "custom";

export default function RecordForm({
  chapter,
  row,
  isDuplicate = false,
  fkOptions,
  projectId,
  onClose,
  onSaved,
}: Props) {
  // A duplicate is a brand-new record pre-filled from an existing one.
  const isEdit = row !== null && !isDuplicate;
  const projectFields = chapter.fields.filter((f) => !f.local);
  const localFields = chapter.fields.filter((f) => f.local);

  const [formData, setFormData] = useState<Row>(() => {
    const data: Row = {};
    for (const f of chapter.fields) {
      if (row) {
        data[f.name] = row[f.name] ?? (f.type === "bool" ? false : "");
      } else if (f.type === "bool") {
        data[f.name] = false;
      } else if (f.name === "quantity") {
        data[f.name] = 1;
      } else if (f.type === "enum" && f.required && f.options) {
        data[f.name] = f.options[0];
      } else {
        data[f.name] = "";
      }
    }
    if (chapter.merge) {
      data[chapter.merge.catalogFkField] = row
        ? row[chapter.merge.catalogFkField] ?? null
        : null;
    }
    return data;
  });

  const [mode, setMode] = useState<Mode>(() => {
    if (!chapter.merge) return "catalog";
    if (row) return row[chapter.merge.catalogFkField] != null ? "catalog" : "custom";
    return "catalog";
  });

  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function set(name: string, value: unknown) {
    setFormData((prev) => ({ ...prev, [name]: value }));
  }

  // ---- value coercion ----------------------------------------------------
  function coerce(field: FieldDef, value: any): unknown {
    if (field.type === "bool") return !!value;
    if (field.type === "number" || field.type === "fk") {
      if (value === "" || value === null || value === undefined) return null;
      const n = Number(value);
      return Number.isNaN(n) ? null : n;
    }
    if (value === "" || value === undefined) return null;
    return value;
  }

  // ---- rendering of a single input --------------------------------------
  function renderInput(field: FieldDef) {
    const value = formData[field.name];

    if (field.type === "textarea") {
      return (
        <textarea
          className="input"
          rows={2}
          value={value ?? ""}
          onChange={(e) => set(field.name, e.target.value)}
        />
      );
    }
    if (field.type === "bool") {
      return (
        <input
          type="checkbox"
          checked={!!value}
          onChange={(e) => set(field.name, e.target.checked)}
        />
      );
    }
    if (field.type === "number") {
      return (
        <input
          className="input"
          type="number"
          value={value ?? ""}
          onChange={(e) => set(field.name, e.target.value)}
        />
      );
    }
    if (field.type === "enum") {
      return (
        <select
          className="input"
          value={value ?? ""}
          onChange={(e) => set(field.name, e.target.value)}
        >
          {!field.required && <option value="">(none)</option>}
          {field.options!.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      );
    }
    if (field.type === "fk") {
      const targetKey = field.fkChapter!;
      const targetLabelField = getChapter(targetKey).fkLabelField;
      let opts = (fkOptions[targetKey] ?? []).map((r) => ({
        value: r.id as number,
        label: String(r[targetLabelField] ?? `#${r.id}`),
      }));
      // A self-referencing FK must not be able to point at the row itself.
      if (row && targetKey === chapter.key) {
        opts = opts.filter((o) => o.value !== row.id);
      }
      const current =
        value === "" || value === null || value === undefined ? null : Number(value);
      return (
        <SearchableSelect
          options={opts}
          value={current}
          onChange={(v) => set(field.name, v)}
        />
      );
    }
    return (
      <input
        className="input"
        value={value ?? ""}
        onChange={(e) => set(field.name, e.target.value)}
      />
    );
  }

  function fieldRow(field: FieldDef, readOnlyValue?: string) {
    return (
      <div className="field" key={field.name}>
        <label>
          {field.label}
          {field.required && <span className="req">*</span>}
        </label>
        {readOnlyValue !== undefined ? (
          <div className="readonly">{readOnlyValue || "—"}</div>
        ) : (
          renderInput(field)
        )}
      </div>
    );
  }

  // ---- merge (catalog) section ------------------------------------------
  function renderMergeSection() {
    if (!chapter.merge) return null;
    const merge = chapter.merge;
    const catalogRows = fkOptions[merge.catalogChapter] ?? [];
    const catalogChapter = getChapter(merge.catalogChapter);

    const catalogOpts = catalogRows.map((r) => ({
      value: r.id as number,
      label: merge.catalogLabelFields
        .map((f) => r[f])
        .filter(Boolean)
        .join("  /  "),
    }));
    const selectedCatalog =
      catalogRows.find((r) => r.id === formData[merge.catalogFkField]) ?? null;

    return (
      <div className="merge-box">
        <div className="merge-toggle">
          <label>
            <input
              type="radio"
              checked={mode === "catalog"}
              onChange={() => setMode("catalog")}
            />
            From catalog
          </label>
          <label>
            <input
              type="radio"
              checked={mode === "custom"}
              onChange={() => setMode("custom")}
            />
            Custom item (no catalog)
          </label>
        </div>

        {mode === "catalog" ? (
          <>
            <div className="field">
              <label>
                Catalog record<span className="req">*</span>
              </label>
              <SearchableSelect
                options={catalogOpts}
                value={formData[merge.catalogFkField] ?? null}
                onChange={(v) => set(merge.catalogFkField, v)}
                placeholder="Search the catalog..."
              />
            </div>
            {selectedCatalog && (
              <div className="catalog-preview">
                <div className="catalog-preview-title">
                  Permanent attributes (from catalog, read-only)
                </div>
                <div className="form-grid">
                  {catalogChapter.fields
                    .filter((f) => f.type !== "textarea")
                    .map((f) =>
                      fieldRow(f, String(selectedCatalog[f.name] ?? "")),
                    )}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="form-grid">
            {localFields.map((f) => fieldRow(f))}
          </div>
        )}
      </div>
    );
  }

  // ---- validation + save -------------------------------------------------
  function validate(): string | null {
    if (chapter.projectScoped && !projectId) {
      return "Select a project before adding project records.";
    }
    for (const f of projectFields) {
      if (f.required) {
        const v = formData[f.name];
        if (v === "" || v === null || v === undefined) {
          return `${f.label} is required.`;
        }
      }
    }
    if (chapter.merge) {
      if (mode === "catalog" && !formData[chapter.merge.catalogFkField]) {
        return "Select a catalog record, or switch to a custom item.";
      }
      if (mode === "custom") {
        const primary = chapter.fields.find(
          (f) => f.name === chapter.merge!.primaryLocalField,
        )!;
        if (!formData[primary.name]) {
          return `${primary.label} is required for a custom item.`;
        }
      }
    }
    return null;
  }

  function buildPayload(): Row {
    const payload: Row = {};
    for (const f of projectFields) {
      payload[f.name] = coerce(f, formData[f.name]);
    }
    if (chapter.projectScoped) {
      payload.project_id = projectId;
    }
    if (chapter.merge) {
      if (mode === "catalog") {
        payload[chapter.merge.catalogFkField] =
          formData[chapter.merge.catalogFkField] ?? null;
        for (const f of localFields) payload[f.name] = null;
      } else {
        payload[chapter.merge.catalogFkField] = null;
        for (const f of localFields) payload[f.name] = coerce(f, formData[f.name]);
      }
    }
    return payload;
  }

  async function handleSave() {
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = buildPayload();
      if (isEdit) {
        await api.update(chapter.key, row!.id, payload);
      } else {
        await api.create(chapter.key, payload);
      }
      onSaved();
    } catch (e: any) {
      setError(e?.message ?? String(e));
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            {isEdit ? "Edit" : isDuplicate ? "Duplicate" : "Add"} —{" "}
            {chapter.title}
          </h3>
          <button className="btn-icon" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {renderMergeSection()}

          {chapter.merge && (
            <div className="section-label">Project-specific fields</div>
          )}
          <div className="form-grid">
            {projectFields.map((f) => fieldRow(f))}
          </div>

          {error && <div className="form-error">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
