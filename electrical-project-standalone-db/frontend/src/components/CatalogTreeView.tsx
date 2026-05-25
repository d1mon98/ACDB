// Hierarchical catalog group tree with expand/collapse and CRUD for items.
//
// Top-level groups expand to show sub-groups; leaf groups show their catalog
// items.  Groups with a `linked_table` map to the existing complex catalog
// tables; all other groups use the generic cat_* table API.

import { useEffect, useState } from "react";
import { api } from "../api";
import type { CatalogGroup, CatalogGroupCreate, CatalogGroupTree, CatalogItem, CatalogItemCreate } from "../types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map group_code suffix → API prefix for linked legacy tables. */
const LINKED_TABLE_SLUG: Record<string, string> = {
  catalog_manufacturers: "catalog-manufacturers",
  catalog_equipment:     "catalog-equipment",
  catalog_cables:        "catalog-cables",
  catalog_instruments:   "catalog-instruments",
  catalog_io_modules:    "catalog-io-modules",
  catalog_devices:       "catalog-devices",
};

/** Map cat_* table name → API slug prefix. */
const CAT_TABLE_SLUG: Record<string, string> = {
  cat_power_systems:       "cat-power-systems",
  cat_voltage_classes:     "cat-voltage-classes",
  cat_grounding_types:     "cat-grounding-types",
  cat_phase_wire_configs:  "cat-phase-wire-configs",
  cat_equipment_types:     "cat-equipment-types",
  cat_equipment_models:    "cat-equipment-models",
  cat_enclosures:          "cat-enclosures",
  cat_mounting_types:      "cat-mounting-types",
  cat_switchgear:          "cat-switchgear",
  cat_switchboards:        "cat-switchboards",
  cat_mccs:                "cat-mccs",
  cat_panelboards:         "cat-panelboards",
  cat_transformers:        "cat-transformers",
  cat_ats:                 "cat-ats",
  cat_generators:          "cat-generators",
  cat_ups:                 "cat-ups",
  cat_breakers:            "cat-breakers",
  cat_fuses:               "cat-fuses",
  cat_relays:              "cat-relays",
  cat_overloads:           "cat-overloads",
  cat_disconnect_switches: "cat-disconnect-switches",
  cat_soft_starters:       "cat-soft-starters",
  cat_vfds:                "cat-vfds",
  cat_conduit_types:       "cat-conduit-types",
  cat_cable_trays:         "cat-cable-trays",
  cat_wire_types:          "cat-wire-types",
  cat_cable_insulations:   "cat-cable-insulations",
  cat_conductor_materials: "cat-conductor-materials",
  cat_instrument_models:   "cat-instrument-models",
  cat_signal_types:        "cat-signal-types",
  cat_measurement_types:   "cat-measurement-types",
  cat_process_connections: "cat-process-connections",
  cat_plcs:                "cat-plcs",
  cat_plc_io:              "cat-plc-io",
  cat_scada:               "cat-scada",
  cat_network_devices:     "cat-network-devices",
  cat_comm_protocols:      "cat-comm-protocols",
  cat_area_types:          "cat-area-types",
  cat_room_types:          "cat-room-types",
  cat_hazardous_areas:     "cat-hazardous-areas",
  cat_environmental_ratings: "cat-environmental-ratings",
  cat_drawing_types:       "cat-drawing-types",
  cat_revision_statuses:   "cat-revision-statuses",
  cat_document_types:      "cat-document-types",
  cat_submittal_statuses:  "cat-submittal-statuses",
  cat_installation_methods:"cat-installation-methods",
  cat_mounting_details:    "cat-mounting-details",
  cat_conduit_routing:     "cat-conduit-routing",
  cat_termination_types:   "cat-termination-types",
};

// ---------------------------------------------------------------------------
// ItemPane: shows items for a selected group node
// ---------------------------------------------------------------------------

function ItemPane({ group }: { group: CatalogGroupTree }) {
  const [items, setItems]     = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [adding, setAdding]   = useState(false);
  const [editId, setEditId]   = useState<number | null>(null);
  const [editName, setEditName] = useState("");

  const slug = group.linked_table
    ? LINKED_TABLE_SLUG[group.linked_table]
    : undefined;

  useEffect(() => {
    setLoading(true);
    setError(null);
    setItems([]);
    if (!slug) {
      setLoading(false);
      setError("No catalog table linked to this group.");
      return;
    }
    api.catalogItems.list(slug, group.linked_table ? undefined : group.id)
      .then((res) => setItems(res.items))
      .catch((e) => setError(e?.message ?? "Load failed."))
      .finally(() => setLoading(false));
  }, [group.id, slug]);

  async function handleAdd() {
    if (!slug || !newCode.trim() || !newName.trim()) return;
    setAdding(true);
    try {
      const body: CatalogItemCreate = {
        catalog_group_id: group.id,
        code: newCode.trim(),
        name: newName.trim(),
        description: null,
        is_active: true,
        notes: null,
      };
      const created = await api.catalogItems.create(slug, body);
      setItems((prev) => [...prev, created]);
      setNewCode("");
      setNewName("");
    } catch (e: any) {
      setError(e?.message ?? "Add failed.");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: number) {
    if (!slug || !confirm("Delete this item?")) return;
    try {
      await api.catalogItems.remove(slug, id);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch (e: any) {
      setError(e?.message ?? "Delete failed.");
    }
  }

  async function handleSaveEdit(id: number) {
    if (!slug) return;
    try {
      const updated = await api.catalogItems.update(slug, id, { name: editName });
      setItems((prev) => prev.map((i) => (i.id === id ? updated : i)));
      setEditId(null);
    } catch (e: any) {
      setError(e?.message ?? "Save failed.");
    }
  }

  return (
    <div className="cat-item-pane">
      <div className="cat-item-pane__header">
        <span className="cat-item-pane__title">{group.group_name}</span>
        {group.description && (
          <span className="cat-item-pane__desc">{group.description}</span>
        )}
      </div>

      {error && <div className="form-error" style={{ margin: "0 0 8px" }}>{error}</div>}

      {loading ? (
        <div className="cat-item-pane__loading">Loading…</div>
      ) : (
        <>
          <table className="cat-item-pane__table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th style={{ width: 80 }}>Active</th>
                <th style={{ width: 80 }}></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan={4} style={{ textAlign: "center", color: "#888" }}>No items yet.</td></tr>
              ) : items.map((item) => (
                <tr key={item.id}>
                  <td><code>{item.code}</code></td>
                  <td>
                    {editId === item.id ? (
                      <input
                        className="erd-panel__input"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") handleSaveEdit(item.id); if (e.key === "Escape") setEditId(null); }}
                        autoFocus
                        style={{ width: "100%" }}
                      />
                    ) : (
                      <span
                        style={{ cursor: "pointer" }}
                        onDoubleClick={() => { setEditId(item.id); setEditName(item.name); }}
                        title="Double-click to edit"
                      >
                        {item.name}
                      </span>
                    )}
                  </td>
                  <td style={{ textAlign: "center" }}>{item.is_active ? "✓" : "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    {editId === item.id ? (
                      <>
                        <button className="btn btn-primary btn-xs" onClick={() => handleSaveEdit(item.id)}>Save</button>
                        {" "}
                        <button className="btn btn-xs" onClick={() => setEditId(null)}>Cancel</button>
                      </>
                    ) : (
                      <button className="btn btn-danger btn-xs" onClick={() => handleDelete(item.id)}>✕</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {slug && (
            <div className="cat-item-pane__add-row">
              <input
                className="erd-panel__input"
                placeholder="Code"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                style={{ width: 100 }}
              />
              <input
                className="erd-panel__input"
                placeholder="Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{ flex: 1 }}
              />
              <button
                className="btn btn-primary"
                onClick={handleAdd}
                disabled={adding || !newCode.trim() || !newName.trim()}
              >
                + Add
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TreeNode: one node in the group tree
// ---------------------------------------------------------------------------

function TreeNode({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: CatalogGroupTree;
  depth: number;
  selected: number | null;
  onSelect: (node: CatalogGroupTree) => void;
}) {
  const [open, setOpen] = useState(depth === 0);
  const hasChildren = node.children.length > 0;
  const isLeaf = !hasChildren;
  const isSelected = selected === node.id;

  return (
    <div className="cat-tree-node">
      <div
        className={`cat-tree-node__row${isSelected ? " cat-tree-node__row--selected" : ""}`}
        style={{ paddingLeft: 12 + depth * 16 }}
        onClick={() => {
          if (hasChildren) setOpen((o) => !o);
          onSelect(node);
        }}
      >
        <span className="cat-tree-node__toggle">
          {hasChildren ? (open ? "▾" : "▸") : "◦"}
        </span>
        <span className="cat-tree-node__name">{node.group_name}</span>
        {isLeaf && node.linked_table && (
          <span className="cat-tree-node__badge" title="Linked to existing catalog table">link</span>
        )}
      </div>
      {hasChildren && open && node.children.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          depth={depth + 1}
          selected={selected}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CatalogTreeView: main component
// ---------------------------------------------------------------------------

export default function CatalogTreeView() {
  const [tree, setTree] = useState<CatalogGroupTree[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CatalogGroupTree | null>(null);

  // Create group form
  const [showAdd, setShowAdd] = useState(false);
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    api.catalogGroups.tree()
      .then(setTree)
      .catch((e) => setError(e?.message ?? "Failed to load catalog groups."))
      .finally(() => setLoading(false));
  }, []);

  async function handleAddGroup() {
    if (!newCode.trim() || !newName.trim()) return;
    setAdding(true);
    try {
      const body: CatalogGroupCreate = {
        parent_group_id: null,
        group_code: newCode.trim(),
        group_name: newName.trim(),
        description: newDesc.trim() || null,
        display_order: 99,
        is_active: true,
        linked_table: null,
        notes: null,
      };
      await api.catalogGroups.create(body);
      const refreshed = await api.catalogGroups.tree();
      setTree(refreshed);
      setShowAdd(false);
      setNewCode("");
      setNewName("");
      setNewDesc("");
    } catch (e: any) {
      setError(e?.message ?? "Create failed.");
    } finally {
      setAdding(false);
    }
  }

  // Determine if selected node is a leaf (no children) — only leaves show items.
  const isLeaf = selected !== null && selected.children.length === 0;

  if (loading) return <div className="catalog-tree__loading">Loading catalog hierarchy…</div>;
  if (error) return <div className="form-error" style={{ margin: 12 }}>{error}</div>;

  return (
    <div className="catalog-tree">
      <div className="catalog-tree__sidebar">
        <div className="catalog-tree__sidebar-header">
          <span className="catalog-tree__title">Catalog Groups</span>
          <button
            className="btn btn-primary btn-xs"
            onClick={() => setShowAdd((s) => !s)}
            title="Add top-level group"
          >
            + Group
          </button>
        </div>

        {showAdd && (
          <div className="catalog-tree__add-form">
            <input className="erd-panel__input" placeholder="Code (unique)" value={newCode}
              onChange={(e) => setNewCode(e.target.value)} />
            <input className="erd-panel__input" placeholder="Name" value={newName}
              onChange={(e) => setNewName(e.target.value)} />
            <input className="erd-panel__input" placeholder="Description (optional)" value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)} />
            <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
              <button className="btn btn-primary" onClick={handleAddGroup} disabled={adding}>
                {adding ? "Adding…" : "Add"}
              </button>
              <button className="btn" onClick={() => setShowAdd(false)}>Cancel</button>
            </div>
          </div>
        )}

        <div className="catalog-tree__nodes">
          {tree.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              depth={0}
              selected={selected?.id ?? null}
              onSelect={setSelected}
            />
          ))}
        </div>
      </div>

      <div className="catalog-tree__content">
        {selected === null ? (
          <div className="catalog-tree__placeholder">
            Select a catalog group to view its items.
          </div>
        ) : isLeaf ? (
          <ItemPane key={selected.id} group={selected} />
        ) : (
          <div className="catalog-tree__placeholder">
            <strong>{selected.group_name}</strong>
            <p>{selected.description}</p>
            <p style={{ color: "#888" }}>Expand a sub-group to view items.</p>
          </div>
        )}
      </div>
    </div>
  );
}
