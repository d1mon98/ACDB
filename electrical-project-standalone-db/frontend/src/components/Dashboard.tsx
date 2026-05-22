// Project dashboard: a count per Class B chapter, so the user can see at a
// glance how completely the database reflects the selected project.

import { useEffect, useState } from "react";
import { api } from "../api";
import type { Row } from "../types";

interface Props {
  projectId: number;
  onNavigate: (chapterKey: string) => void;
}

// Each card maps a dashboard response field to the chapter it opens.
const CARDS = [
  { chapterKey: "project-locations", label: "Locations", field: "locations" },
  { chapterKey: "project-equipment", label: "Equipment", field: "equipment" },
  { chapterKey: "project-panel-circuits", label: "Panel Circuits", field: "panel_circuits" },
  { chapterKey: "project-cables", label: "Cables", field: "cables" },
  { chapterKey: "project-instruments", label: "Instruments", field: "instruments" },
  { chapterKey: "project-io-list", label: "I/O List", field: "io_points" },
  { chapterKey: "project-control-panels", label: "Control Panels", field: "control_panels" },
  { chapterKey: "project-panel-components", label: "Panel Components", field: "panel_components" },
];

export default function Dashboard({ projectId, onNavigate }: Props) {
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setError(null);
    api
      .dashboard(projectId)
      .then(setData)
      .catch((e: any) => setError(e?.message ?? String(e)));
  }, [projectId]);

  if (error) return <div className="form-error">{error}</div>;
  if (!data) return <div className="empty">Loading…</div>;

  return (
    <div className="chapter">
      <div className="chapter-head">
        <div>
          <h2>Dashboard — {data.project.name}</h2>
          <div className="chapter-sub">
            {data.project.project_number} · {data.project.status} ·{" "}
            {data.total} project record(s) total
          </div>
        </div>
      </div>

      <div className="dash-grid">
        {CARDS.map((card) => (
          <div
            key={card.chapterKey}
            className="dash-card"
            onClick={() => onNavigate(card.chapterKey)}
          >
            <div className="dash-count">{data[card.field] ?? 0}</div>
            <div className="dash-label">{card.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
