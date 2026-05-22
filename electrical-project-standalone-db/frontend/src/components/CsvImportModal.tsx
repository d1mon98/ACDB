// CSV import dialog.
//
// Accepts a CSV file (or pasted CSV text), posts it to the table's import
// endpoint, and reports how many rows were created and any per-row errors.
// The column headers must match the table's field names -- exporting the table
// first gives a ready-made template.

import { useState } from "react";
import { api } from "../api";
import type { ChapterDef } from "../types";

interface Props {
  chapter: ChapterDef;
  projectId: number | null;
  onClose: () => void;
  onImported: () => void;
}

interface ImportResult {
  created: number;
  errors: { row: number; error: string }[];
}

export default function CsvImportModal({
  chapter,
  projectId,
  onClose,
  onImported,
}: Props) {
  const [content, setContent] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => setContent(String(reader.result ?? ""));
    reader.readAsText(file);
  }

  async function handleImport() {
    if (!content.trim()) {
      setError("Choose a CSV file or paste CSV text first.");
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const params: Record<string, unknown> = {};
      if (chapter.projectScoped) params.project_id = projectId;
      const res = await api.importCsv(chapter.key, content, params);
      setResult(res);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={() => !busy && onClose()}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Import CSV — {chapter.title}</h3>
          <button className="btn-icon" onClick={() => !busy && onClose()}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {!result && (
            <>
              <div className="field-hint" style={{ marginBottom: 10 }}>
                CSV column headers must match the field names. Tip: use{" "}
                <strong>Export CSV</strong> first to get a template with the
                correct columns. <code>id</code> and timestamp columns are
                ignored.
              </div>
              <div className="field">
                <label>CSV file</label>
                <input type="file" accept=".csv,text/csv" onChange={handleFile} />
              </div>
              <div className="field">
                <label>…or paste CSV text</label>
                <textarea
                  className="input"
                  rows={6}
                  value={content}
                  placeholder="drawing_number,title,drawing_type&#10;E-001,One-Line,ONE_LINE"
                  onChange={(e) => {
                    setContent(e.target.value);
                    setFileName(null);
                  }}
                />
              </div>
              {fileName && (
                <div className="field-hint">Loaded file: {fileName}</div>
              )}
            </>
          )}

          {result && (
            <div>
              <div
                className={
                  result.errors.length ? "form-error" : "form-success"
                }
              >
                {result.created} row(s) created.
                {result.errors.length > 0 &&
                  ` ${result.errors.length} row(s) failed.`}
              </div>
              {result.errors.length > 0 && (
                <table className="grid" style={{ marginTop: 10 }}>
                  <thead>
                    <tr>
                      <th className="col-id">Row</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.errors.map((er) => (
                      <tr key={er.row}>
                        <td className="col-id">{er.row}</td>
                        <td>{er.error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {error && <div className="form-error">{error}</div>}
        </div>

        <div className="modal-footer">
          {result ? (
            <button className="btn btn-primary" onClick={onImported}>
              Done
            </button>
          ) : (
            <>
              <button className="btn" onClick={onClose} disabled={busy}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={busy}
              >
                {busy ? "Importing…" : "Import"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
