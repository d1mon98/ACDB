// Left-hand navigation with an inline collapsible System Catalogs tree.
// Folders (branch nodes) are bold; leaf tables are italic.
// Each node has hover-revealed Create / Edit / Delete actions.
// Nodes are draggable — drop onto another node to reparent, or onto the
// root drop-zone to move to the top level.

import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { PROJECT_CHAPTERS } from "../chapters";
import type { CatalogGroupCreate, CatalogGroupTree } from "../types";

interface Props {
  active: string;
  onSelect: (key: string) => void;
  width: number;
}

const ROOT = "root" as const;

// ---------------------------------------------------------------------------
// Tree helpers
// ---------------------------------------------------------------------------

function findNode(nodes: CatalogGroupTree[], id: number): CatalogGroupTree | null {
  for (const n of nodes) {
    if (n.id === id) return n;
    const found = findNode(n.children, id);
    if (found) return found;
  }
  return null;
}

function subtreeContains(nodes: CatalogGroupTree[], id: number): boolean {
  for (const n of nodes) {
    if (n.id === id) return true;
    if (subtreeContains(n.children, id)) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Inline add form — must be at module level so React sees a stable type.
// Defining it inside Sidebar would remount on every keystroke (new type each
// render) and the useEffect auto-focus would steal focus back to Code.
// ---------------------------------------------------------------------------

interface AddFormProps {
  parentId: number | null;
  depth: number;
  newCode: string;
  newName: string;
  newDesc: string;
  onCodeChange: (v: string) => void;
  onNameChange: (v: string) => void;
  onDescChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
}

function AddForm({ parentId: _parentId, depth, newCode, newName, newDesc, onCodeChange, onNameChange, onDescChange, onSave, onCancel }: AddFormProps) {
  const codeRef = useRef<HTMLInputElement>(null);
  useEffect(() => { codeRef.current?.focus(); }, []);
  return (
    <div className="nav-tree-add-form" style={{ paddingLeft: 12 + depth * 12 }}>
      <input ref={codeRef} className="nav-tree-input" placeholder="Code (unique)"
        value={newCode} onChange={(e) => onCodeChange(e.target.value)} />
      <input className="nav-tree-input" placeholder="Name"
        value={newName} onChange={(e) => onNameChange(e.target.value)} />
      <input className="nav-tree-input" placeholder="Description (optional)"
        value={newDesc} onChange={(e) => onDescChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onSave();
          if (e.key === "Escape") onCancel();
        }} />
      <div style={{ display: "flex", gap: 4, marginTop: 2 }}>
        <button className="nav-tree-btn nav-tree-btn--save"
          onClick={onSave}
          disabled={!newCode.trim() || !newName.trim()}>Save</button>
        <button className="nav-tree-btn" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Sidebar({ active, onSelect, width }: Props) {
  const [tree, setTree]           = useState<CatalogGroupTree[]>([]);
  const [openIds, setOpenIds]     = useState<Set<number>>(new Set());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editCode, setEditCode]   = useState("");
  const [editName, setEditName]   = useState("");
  const [editDesc, setEditDesc]   = useState("");
  const [addingUnder, setAddingUnder] = useState<typeof ROOT | number | null>(null);
  const [newCode, setNewCode]     = useState("");
  const [newName, setNewName]     = useState("");
  const [newDesc, setNewDesc]     = useState("");

  // drag-and-drop
  const [dragId, setDragId]       = useState<number | null>(null);
  const [dragOverId, setDragOverId] = useState<number | typeof ROOT | null>(null);
  const [dropError, setDropError] = useState<string | null>(null);

  // Use a ref so drag callbacks always see the latest tree without stale closure.
  const treeRef = useRef(tree);
  useEffect(() => { treeRef.current = tree; }, [tree]);

  function refresh() {
    api.catalogGroups.tree().then(setTree).catch(() => {});
  }
  useEffect(() => { refresh(); }, []);

  function toggleOpen(id: number) {
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function openAddForm(under: typeof ROOT | number) {
    setAddingUnder(under);
    setNewCode(""); setNewName(""); setNewDesc("");
    setEditingId(null);
  }

  // ---- CRUD handlers -------------------------------------------------------

  async function handleAdd(parentId: number | null) {
    if (!newCode.trim() || !newName.trim()) return;
    const body: CatalogGroupCreate = {
      parent_group_id: parentId,
      group_code: newCode.trim(),
      group_name: newName.trim(),
      description: newDesc.trim() || null,
      display_order: 99,
      is_active: true,
      linked_table: null,
      notes: null,
    };
    await api.catalogGroups.create(body);
    setAddingUnder(null);
    setNewCode(""); setNewName(""); setNewDesc("");
    if (typeof parentId === "number") {
      setOpenIds((prev) => new Set(prev).add(parentId));
    }
    refresh();
  }

  async function handleSaveEdit(id: number) {
    if (!editName.trim()) { setEditingId(null); return; }
    await api.catalogGroups.update(id, {
      group_code: editCode.trim() || undefined,
      group_name: editName.trim(),
      description: editDesc.trim() || null,
    });
    setEditingId(null);
    refresh();
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Delete "${name}"? Sub-groups will also be removed.`)) return;
    await api.catalogGroups.remove(id);
    if (active === `group:${id}`) onSelect("database");
    refresh();
  }

  // ---- drag-and-drop -------------------------------------------------------

  function canDrop(targetId: number | null): boolean {
    if (dragId === null) return false;
    if (targetId === dragId) return false;
    if (targetId !== null) {
      const dragNode = findNode(treeRef.current, dragId);
      if (dragNode && subtreeContains(dragNode.children, targetId)) return false;
    }
    return true;
  }

  async function handleDrop(targetParentId: number | null) {
    if (dragId === null || !canDrop(targetParentId)) return;
    const id = dragId;
    setDragId(null);
    setDragOverId(null);
    try {
      await api.catalogGroups.update(id, { parent_group_id: targetParentId });
      if (targetParentId !== null) {
        setOpenIds((prev) => new Set(prev).add(targetParentId));
      }
      refresh();
    } catch (e: any) {
      setDropError(e?.message ?? "Move failed.");
    }
  }

  async function handleMove(node: CatalogGroupTree, siblings: CatalogGroupTree[], direction: "up" | "down") {
    const sorted = [...siblings].sort((a, b) => a.display_order - b.display_order || a.id - b.id);
    const idx = sorted.findIndex((s) => s.id === node.id);
    const targetIdx = direction === "up" ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= sorted.length) return;
    // Assign clean display_orders (0, 10, 20, …) then swap the two moving nodes.
    const orders = sorted.map((_, i) => i * 10);
    [orders[idx], orders[targetIdx]] = [orders[targetIdx], orders[idx]];
    try {
      await Promise.all(sorted.map((n, i) => api.catalogGroups.update(n.id, { display_order: orders[i] })));
      refresh();
    } catch (e: any) {
      setDropError(e?.message ?? "Reorder failed.");
    }
  }


  // ---- recursive tree node --------------------------------------------------

  function renderNode(node: CatalogGroupTree, depth: number, siblings: CatalogGroupTree[]): React.ReactNode {
    const hasChildren = node.children.length > 0;
    const navKey   = `group:${node.id}`;
    const isActive = !hasChildren && active === navKey;
    const isOpen   = openIds.has(node.id);
    const isEditing = editingId === node.id;
    const basePad  = 12 + depth * 12;
    const rowPad   = isActive ? basePad - 3 : basePad;
    const sorted   = [...siblings].sort((a, b) => a.display_order - b.display_order || a.id - b.id);
    const sibIdx   = sorted.findIndex((s) => s.id === node.id);
    const isFirst  = sibIdx === 0;
    const isLast   = sibIdx === sorted.length - 1;

    const isDragging  = dragId === node.id;
    const isDragOver  = dragOverId === node.id && canDrop(node.id);

    return (
      <div key={node.id}>
        {/* ---- node row ---- */}
        <div
          className={
            "nav-tree-row" +
            (isActive    ? " nav-active"            : "") +
            (isDragging  ? " nav-tree-row--dragging" : "") +
            (isDragOver  ? " nav-tree-row--drag-over" : "")
          }
          style={{ paddingLeft: rowPad }}
          draggable={!isEditing}
          onDragStart={(e) => {
            e.stopPropagation();
            setDragId(node.id);
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", String(node.id));
          }}
          onDragEnd={() => { setDragId(null); setDragOverId(null); }}
          onDragOver={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (canDrop(node.id)) {
              e.dataTransfer.dropEffect = "move";
              setDragOverId(node.id);
            } else {
              e.dataTransfer.dropEffect = "none";
            }
          }}
          onDragLeave={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node)) {
              setDragOverId((prev) => (prev === node.id ? null : prev));
            }
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleDrop(node.id);
          }}
        >
          {isEditing ? (
            <div className="nav-tree-edit-form">
              <input className="nav-tree-input" placeholder="Code"
                value={editCode} onChange={(e) => setEditCode(e.target.value)} autoFocus />
              <input className="nav-tree-input" placeholder="Name"
                value={editName} onChange={(e) => setEditName(e.target.value)} />
              <input className="nav-tree-input" placeholder="Description (optional)"
                value={editDesc} onChange={(e) => setEditDesc(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveEdit(node.id);
                  if (e.key === "Escape") setEditingId(null);
                }} />
              <div style={{ display: "flex", gap: 4, marginTop: 2 }}>
                <button className="nav-tree-btn nav-tree-btn--save"
                  onClick={() => handleSaveEdit(node.id)}>✓ Save</button>
                <button className="nav-tree-btn"
                  onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <button
                className={
                  "nav-tree-label" +
                  (hasChildren ? " nav-tree-label--folder" : " nav-tree-label--leaf")
                }
                onClick={() => { if (hasChildren) toggleOpen(node.id); else onSelect(navKey); }}
              >
                <span className="nav-tree-toggle">
                  {hasChildren ? (isOpen ? "▾" : "▸") : "◦"}
                </span>
                {node.group_name}
              </button>

              <div className="nav-tree-actions">
                <button className="nav-tree-btn" title="Move up"
                  disabled={isFirst}
                  onClick={(e) => { e.stopPropagation(); handleMove(node, siblings, "up"); }}>↑</button>
                <button className="nav-tree-btn" title="Move down"
                  disabled={isLast}
                  onClick={(e) => { e.stopPropagation(); handleMove(node, siblings, "down"); }}>↓</button>
                <button className="nav-tree-btn" title="Add sub-group"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (hasChildren && !isOpen) toggleOpen(node.id);
                    openAddForm(node.id);
                  }}>+</button>
                <button className="nav-tree-btn" title="Edit"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingId(node.id);
                    setEditCode(node.group_code);
                    setEditName(node.group_name);
                    setEditDesc(node.description ?? "");
                    setAddingUnder(null);
                  }}>✎</button>
                <button className="nav-tree-btn nav-tree-btn--danger" title="Delete"
                  onClick={(e) => { e.stopPropagation(); handleDelete(node.id, node.group_name); }}>✕</button>
              </div>
            </>
          )}
        </div>

        {/* children */}
        {hasChildren && isOpen && node.children.map((child) => renderNode(child, depth + 1, node.children))}
        {addingUnder === node.id && (
          <AddForm
            parentId={node.id} depth={depth + 1}
            newCode={newCode} newName={newName} newDesc={newDesc}
            onCodeChange={setNewCode} onNameChange={setNewName} onDescChange={setNewDesc}
            onSave={() => handleAdd(node.id)} onCancel={() => setAddingUnder(null)}
          />
        )}
      </div>
    );
  }

  // ---- flat chapter button --------------------------------------------------

  function item(key: string, label: string) {
    return (
      <button key={key}
        className={"nav-item" + (active === key ? " nav-active" : "")}
        onClick={() => onSelect(key)}
      >{label}</button>
    );
  }

  // ---- render ---------------------------------------------------------------

  return (
    <nav className="sidebar" style={{ width }}>
      {item("database", "Database Browser")}
      {item("dashboard", "Dashboard")}
      {item("erd", "Relationship Diagram")}

      <div className="nav-group nav-group--with-btn">
        <span>System Catalogs</span>
        <button className="nav-tree-btn nav-tree-btn--section"
          title="Add top-level catalog group"
          onClick={() => openAddForm(ROOT)}>+</button>
      </div>

      {dropError && (
        <div className="nav-tree-drop-error" onClick={() => setDropError(null)}>
          {dropError} ✕
        </div>
      )}

      {tree.map((node) => renderNode(node, 0, tree))}
      {addingUnder === ROOT && (
        <AddForm
          parentId={null} depth={0}
          newCode={newCode} newName={newName} newDesc={newDesc}
          onCodeChange={setNewCode} onNameChange={setNewName} onDescChange={setNewDesc}
          onSave={() => handleAdd(null)} onCancel={() => setAddingUnder(null)}
        />
      )}

      {/* Root-level drop zone — visible only while dragging */}
      {dragId !== null && (
        <div
          className={"nav-tree-root-drop" + (dragOverId === ROOT ? " nav-tree-root-drop--active" : "")}
          onDragOver={(e) => {
            e.preventDefault();
            if (canDrop(null)) { e.dataTransfer.dropEffect = "move"; setDragOverId(ROOT); }
          }}
          onDragLeave={() => setDragOverId((prev) => (prev === ROOT ? null : prev))}
          onDrop={(e) => { e.preventDefault(); handleDrop(null); }}
        >
          ↑ Move to top level
        </div>
      )}

      <div className="nav-group">Project Tables</div>
      {PROJECT_CHAPTERS.map((c) => item(c.key, c.title))}
    </nav>
  );
}
