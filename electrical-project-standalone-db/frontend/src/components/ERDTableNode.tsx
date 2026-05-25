// Custom React Flow node that renders one database table as a card.
//
// Header shows the table name with a collapse toggle.
// Body lists every column with its type, PK badge, and NOT NULL indicator.
// Handles on all four sides let edges connect from any direction.

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import type { ErdTableNodeData } from "../types";

function ERDTableNode({ data, selected }: NodeProps) {
  const { tableName, columns, collapsed } = data as unknown as ErdTableNodeData;

  return (
    <div className={`erd-node${selected ? " erd-node--selected" : ""}`}>
      {/* Connection handles on all four sides */}
      <Handle type="target" position={Position.Top}    id="top"    className="erd-handle" />
      <Handle type="source" position={Position.Bottom} id="bottom" className="erd-handle" />
      <Handle type="target" position={Position.Left}   id="left"   className="erd-handle" />
      <Handle type="source" position={Position.Right}  id="right"  className="erd-handle" />

      {/* Table header */}
      <div className="erd-node__header">
        <span className="erd-node__icon">▦</span>
        <span className="erd-node__title" title={tableName}>{tableName}</span>
        <span className="erd-node__count">{columns.length}</span>
      </div>

      {/* Column list */}
      {!collapsed && (
        <div className="erd-node__body">
          {columns.map((col) => (
            <div key={col.cid} className={`erd-node__col${col.pk ? " erd-node__col--pk" : ""}`}>
              <span className="erd-node__col-badge">
                {col.pk ? "PK" : col.notnull ? "NN" : ""}
              </span>
              <span className="erd-node__col-name" title={col.name}>{col.name}</span>
              <span className="erd-node__col-type">{col.type || "—"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default memo(ERDTableNode);
