// ERD canvas -- the main Entity Relationship Diagram view.
//
// Displays every table in the connected database as a draggable node.
// FK-derived edges (from SQLite PRAGMA) are shown in blue (read-only).
// User-defined relationships (from erd_relationships) are shown in orange (editable).
//
// Toolbar:  Fit View | Auto-layout | Collapse All | Expand All | + Relationship
// Panel:    click any edge to open RelationshipPanel

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import type {
  Connection,
  Edge,
  Node,
  NodeTypes,
  OnConnect,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import dagre from "@dagrejs/dagre";

import { api } from "../api";
import type {
  ErdEdgeData,
  ErdLayout,
  ErdRelationship,
  ErdSchema,
  ErdTableNodeData,
} from "../types";
import ERDTableNode from "./ERDTableNode";
import RelationshipPanel from "./RelationshipPanel";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NODE_W = 240;
const NODE_H_BASE = 48;      // header only (collapsed)
const NODE_H_ROW  = 24;      // per column row

const nodeTypes: NodeTypes = { tableNode: ERDTableNode as any };

// ---------------------------------------------------------------------------
// Dagre auto-layout
// ---------------------------------------------------------------------------

function autoLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", nodesep: 60, ranksep: 120 });

  nodes.forEach((n) => {
    const nd = n.data as unknown as ErdTableNodeData;
    const rowCount = nd.collapsed ? 0 : nd.columns.length;
    const h = NODE_H_BASE + rowCount * NODE_H_ROW;
    g.setNode(n.id, { width: NODE_W, height: h });
  });
  edges.forEach((e) => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return nodes.map((n) => {
    const { x, y } = g.node(n.id);
    return { ...n, position: { x: x - NODE_W / 2, y: y - NODE_H_BASE / 2 } };
  });
}

// ---------------------------------------------------------------------------
// Build React Flow nodes & edges from API data
// ---------------------------------------------------------------------------

function buildNodes(schema: ErdSchema, layout: ErdLayout): Node[] {
  return Object.entries(schema).map(([tableName, def], i) => {
    const saved = layout[tableName];
    const position = saved
      ? { x: saved.x, y: saved.y }
      : { x: (i % 5) * (NODE_W + 80), y: Math.floor(i / 5) * 320 };
    return {
      id:       tableName,
      type:     "tableNode",
      position,
      data: {
        tableName,
        columns:   def.columns,
        collapsed: saved?.collapsed ?? false,
      } as ErdTableNodeData,
    };
  });
}

function buildFkEdges(schema: ErdSchema): Edge[] {
  const edges: Edge[] = [];
  Object.entries(schema).forEach(([childTable, def]) => {
    def.foreign_keys.forEach((fk) => {
      const edgeId = `fk-${childTable}-${fk.id}`;
      edges.push({
        id:     edgeId,
        source: fk.ref_table,
        target: childTable,
        label:  fk.from_col,
        type:   "smoothstep",
        markerEnd: { type: "arrowclosed" as any },
        style:  { stroke: "#3b82f6", strokeWidth: 1.5 },
        labelStyle:    { fontSize: 10, fill: "#3b82f6" },
        labelBgStyle:  { fill: "#eff6ff", fillOpacity: 0.9 },
        data: {
          source:        "fk",
          rel_type:      "ONE_TO_MANY",
          cascade_update: fk.on_update,
          cascade_delete: fk.on_delete,
          from_col:      fk.from_col,
          to_col:        fk.to_col,
        } as ErdEdgeData,
      });
    });
  });
  return edges;
}

function buildUserEdges(rels: ErdRelationship[]): Edge[] {
  return rels.map((r) => ({
    id:     `user-${r.id}`,
    source: r.parent_table,
    target: r.child_table,
    label:  r.label ?? r.rel_type,
    type:   "smoothstep",
    markerEnd: { type: "arrowclosed" as any },
    style:  { stroke: "#f59e0b", strokeWidth: 2, strokeDasharray: "6 3" },
    labelStyle:   { fontSize: 10, fill: "#b45309" },
    labelBgStyle: { fill: "#fffbeb", fillOpacity: 0.9 },
    data: {
      source:        "user",
      rel_type:      r.rel_type,
      cascade_update: r.cascade_update,
      cascade_delete: r.cascade_delete,
      label:         r.label,
      rel_id:        r.id,
      from_col:      r.foreign_key ?? undefined,
    } as ErdEdgeData,
  }));
}

// ---------------------------------------------------------------------------
// CreateRelModal — quick form to add a new user-defined relationship
// ---------------------------------------------------------------------------

interface CreateRelModalProps {
  tables: string[];
  onSave: (rel: ErdRelationship) => void;
  onClose: () => void;
}

function CreateRelModal({ tables, onSave, onClose }: CreateRelModalProps) {
  const [parent, setParent] = useState(tables[0] ?? "");
  const [child,  setChild]  = useState(tables[1] ?? "");
  const [fk,     setFk]     = useState("");
  const [type,   setType]   = useState<string>("ONE_TO_MANY");
  const [label,  setLabel]  = useState("");
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const rel = await api.erd.createRelationship({
        parent_table:   parent,
        child_table:    child,
        foreign_key:    fk || null,
        rel_type:       type as any,
        cascade_update: "NO ACTION",
        cascade_delete: "NO ACTION",
        label:          label || null,
        notes:          null,
      });
      onSave(rel);
    } catch (e: any) {
      setError(e?.message ?? "Create failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="erd-modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="erd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="erd-panel__header">
          <span className="erd-panel__title">New Relationship</span>
          <button className="erd-panel__close" onClick={onClose}>✕</button>
        </div>
        <div className="erd-panel__body">
          <label className="erd-panel__label">Parent table
            <select className="erd-panel__input" value={parent} onChange={(e) => setParent(e.target.value)}>
              {tables.map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <label className="erd-panel__label">Child table
            <select className="erd-panel__input" value={child} onChange={(e) => setChild(e.target.value)}>
              {tables.map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <label className="erd-panel__label">Foreign key column (optional)
            <input className="erd-panel__input" value={fk} onChange={(e) => setFk(e.target.value)} />
          </label>
          <label className="erd-panel__label">Relationship type
            <select className="erd-panel__input" value={type} onChange={(e) => setType(e.target.value)}>
              {["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_MANY"].map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <label className="erd-panel__label">Label (optional)
            <input className="erd-panel__input" value={label} onChange={(e) => setLabel(e.target.value)} />
          </label>
        </div>
        {error && <div className="form-error" style={{ margin: "0 12px 8px" }}>{error}</div>}
        <div className="erd-panel__footer">
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inner canvas (must be inside <ReactFlowProvider>)
// ---------------------------------------------------------------------------

function ERDInner() {
  const { fitView } = useReactFlow();

  const [schema,     setSchema]     = useState<ErdSchema>({});
  const [userRels,   setUserRels]   = useState<ErdRelationship[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [loadError,  setLoadError]  = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Selected edge (for RelationshipPanel)
  const [selEdge,      setSelEdge]      = useState<Edge | null>(null);
  const [panelSourceT, setPanelSourceT] = useState("");
  const [panelTargetT, setPanelTargetT] = useState("");

  // Create-relationship modal
  const [showCreate, setShowCreate] = useState(false);

  // Debounce position saves
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // -------------------------------------------------------------------------
  // Load data
  // -------------------------------------------------------------------------

  useEffect(() => {
    (async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const [sch, layout, rels] = await Promise.all([
          api.erd.schema(),
          api.erd.getLayout(),
          api.erd.listRelationships(),
        ]);
        setSchema(sch);
        setUserRels(rels);

        let builtNodes = buildNodes(sch, layout);
        const fkEdges   = buildFkEdges(sch);
        const userEdges = buildUserEdges(rels);

        // Auto-layout only if no positions saved yet
        if (Object.keys(layout).length === 0) {
          builtNodes = autoLayout(builtNodes, [...fkEdges, ...userEdges]);
        }

        setNodes(builtNodes);
        setEdges([...fkEdges, ...userEdges]);
      } catch (e: any) {
        setLoadError(e?.message ?? "Failed to load ERD data.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // -------------------------------------------------------------------------
  // Save positions after drag
  // -------------------------------------------------------------------------

  const onNodeDragStop = useCallback((_evt: unknown, _node: unknown, allNodes: Node[]) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const positions: ErdLayout = {};
      allNodes.forEach((n) => {
        const nd = n.data as unknown as ErdTableNodeData;
        positions[n.id] = {
          x:         n.position.x,
          y:         n.position.y,
          collapsed: nd.collapsed,
        };
      });
      api.erd.saveLayout(positions).catch(() => {});
    }, 600);
  }, []);

  // -------------------------------------------------------------------------
  // Connecting nodes creates a new user relationship
  // -------------------------------------------------------------------------

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      // Immediately add a placeholder edge; the modal will persist it
      setEdges((eds) => addEdge({ ...connection, type: "smoothstep" }, eds));
    },
    [setEdges],
  );

  // -------------------------------------------------------------------------
  // Edge click → open properties panel
  // -------------------------------------------------------------------------

  const onEdgeClick = useCallback((_evt: unknown, edge: Edge) => {
    setSelEdge(edge);
    setPanelSourceT(edge.source);
    setPanelTargetT(edge.target);
  }, []);

  // -------------------------------------------------------------------------
  // Toolbar actions
  // -------------------------------------------------------------------------

  function handleFitView() {
    fitView({ padding: 0.1, duration: 300 });
  }

  function handleAutoLayout() {
    setNodes((nds) => {
      const laid = autoLayout(nds, edges);
      // Persist new positions
      const positions: ErdLayout = {};
      laid.forEach((n) => {
        const nd = n.data as unknown as ErdTableNodeData;
        positions[n.id] = {
          x: n.position.x,
          y: n.position.y,
          collapsed: nd.collapsed,
        };
      });
      api.erd.saveLayout(positions).catch(() => {});
      return laid;
    });
    setTimeout(() => fitView({ padding: 0.1, duration: 400 }), 50);
  }

  function toggleCollapseAll(collapsed: boolean) {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...(n.data as unknown as ErdTableNodeData), collapsed } as unknown as Record<string, unknown>,
      })),
    );
  }

  // -------------------------------------------------------------------------
  // Relationship panel callbacks
  // -------------------------------------------------------------------------

  function handleRelDeleted(relId: number) {
    setUserRels((rs) => rs.filter((r) => r.id !== relId));
    setEdges((eds) => eds.filter((e) => e.id !== `user-${relId}`));
    setSelEdge(null);
  }

  function handleRelUpdated(rel: ErdRelationship) {
    setUserRels((rs) => rs.map((r) => (r.id === rel.id ? rel : r)));
    const newEdge = buildUserEdges([rel])[0];
    setEdges((eds) => eds.map((e) => (e.id === `user-${rel.id}` ? newEdge : e)));
    setSelEdge(newEdge);
  }

  function handleRelCreated(rel: ErdRelationship) {
    setUserRels((rs) => [...rs, rel]);
    const newEdge = buildUserEdges([rel])[0];
    setEdges((eds) => [...eds, newEdge]);
    setShowCreate(false);
  }

  const tableNames = useMemo(() => Object.keys(schema).sort(), [schema]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  if (loading) {
    return <div className="empty">Loading schema…</div>;
  }
  if (loadError) {
    return <div className="form-error" style={{ padding: 24 }}>{loadError}</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Toolbar */}
      <div className="erd-toolbar">
        <span className="erd-toolbar__title">Entity Relationship Diagram</span>
        <div className="erd-toolbar__actions">
          <button className="btn" onClick={handleFitView} title="Fit all nodes into view">
            Fit View
          </button>
          <button className="btn" onClick={handleAutoLayout} title="Auto-arrange nodes with Dagre">
            Auto-layout
          </button>
          <button className="btn" onClick={() => toggleCollapseAll(true)}>
            Collapse All
          </button>
          <button className="btn" onClick={() => toggleCollapseAll(false)}>
            Expand All
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + Relationship
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="erd-legend">
        <span className="erd-legend__item erd-legend__item--fk">— FK (schema)</span>
        <span className="erd-legend__item erd-legend__item--user">– – User-defined</span>
        <span className="erd-legend__hint">Click a connector to view/edit · Drag nodes to reposition · Scroll to zoom</span>
      </div>

      {/* Canvas + side panel */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <div style={{ flex: 1, position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onEdgeClick={onEdgeClick}
            onPaneClick={() => setSelEdge(null)}
            fitView
            fitViewOptions={{ padding: 0.1 }}
            minZoom={0.1}
            maxZoom={2}
            defaultEdgeOptions={{ type: "smoothstep" }}
          >
            <Background color="#e5e7eb" gap={20} />
            <Controls />
            <MiniMap
              nodeColor="#3b82f6"
              maskColor="rgba(0,0,0,0.06)"
              style={{ border: "1px solid #e5e7eb" }}
            />
          </ReactFlow>
        </div>

        {/* Properties panel */}
        {selEdge && (
          <RelationshipPanel
            edgeId={selEdge.id}
            edgeData={selEdge.data as unknown as ErdEdgeData}
            sourceTable={panelSourceT}
            targetTable={panelTargetT}
            onClose={() => setSelEdge(null)}
            onDeleted={handleRelDeleted}
            onUpdated={handleRelUpdated}
          />
        )}
      </div>

      {/* Create relationship modal */}
      {showCreate && (
        <CreateRelModal
          tables={tableNames}
          onSave={handleRelCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Public export — wraps ERDInner in the required ReactFlowProvider
// ---------------------------------------------------------------------------

import { ReactFlowProvider } from "@xyflow/react";

export default function ERDCanvas() {
  return (
    <ReactFlowProvider>
      <ERDInner />
    </ReactFlowProvider>
  );
}
