// Shared TypeScript types.
//
// Row data is intentionally loose (Record<string, any>): this is a generic
// data-management tool driven by the chapter metadata in chapters.ts, so the
// UI works the same way for every table without a hand-written type per table.

export type Row = Record<string, any>;

export type FieldType = "text" | "textarea" | "number" | "enum" | "bool" | "fk";

/** One editable field of a table. */
export interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  /** Allowed values, for type "enum". */
  options?: string[];
  /** Chapter key supplying the dropdown options, for type "fk". */
  fkChapter?: string;
  /** True for a local_* permanent attribute (editable only in custom mode). */
  local?: boolean;
}

/** Merge configuration for a catalog-linked Class B table. */
export interface MergeConfig {
  /** Chapter key of the Class A catalog this table merges from. */
  catalogChapter: string;
  /** Foreign-key column pointing at the catalog row. */
  catalogFkField: string;
  /** Catalog fields concatenated to label a catalog option. */
  catalogLabelFields: string[];
  /** Local field that must be filled for a custom (no-catalog) row. */
  primaryLocalField: string;
}

/** A "chapter" -- one database table as presented in the UI. */
export interface ChapterDef {
  /** URL slug; matches the REST endpoint, e.g. "catalog-equipment". */
  key: string;
  title: string;
  /** Class A catalog or Class B project table. */
  group: "catalog" | "project";
  /** True when the chapter is filtered by the selected project. */
  projectScoped: boolean;
  /** Field shown when a row of this chapter is referenced by a foreign key. */
  fkLabelField: string;
  /** Present only on the five catalog-linked Class B tables. */
  merge?: MergeConfig;
  /** All editable fields (project-specific first, then local_* fields). */
  fields: FieldDef[];
  /** Field names (or the special "__source__") to show as grid columns. */
  gridFields: string[];
}

export interface ListResponse<T = Row> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/** One database file managed by the Database Browser. */
export interface DatabaseInfo {
  name: string;
  path: string;
  size_bytes: number;
  modified: string;
  connected: boolean;
}

/** A recently opened database. */
export interface RecentDatabase {
  path: string;
  name: string;
  exists: boolean;
}

/** Which database, if any, is currently connected for a given role. */
export interface ConnectionStatus {
  /** "catalog" or "project" (empty string before first refresh). */
  role: string;
  connected: boolean;
  current: string | null;
  path: string | null;
}

export interface DatabaseListResponse extends ConnectionStatus {
  items: DatabaseInfo[];
  recent: RecentDatabase[];
}

/** A directory or file entry from the filesystem browse endpoint. */
export interface FsEntry {
  name: string;
  path: string;
  size_bytes?: number | null;
  modified?: string | null;
}

// ---------------------------------------------------------------------------
// ERD types
// ---------------------------------------------------------------------------

export interface ErdColumn {
  cid: number;
  name: string;
  type: string;
  notnull: boolean;
  default: string | null;
  pk: boolean;
}

export interface ErdForeignKey {
  id: number;
  seq: number;
  ref_table: string;
  from_col: string;
  to_col: string;
  on_update: string;
  on_delete: string;
}

export interface ErdTableSchema {
  columns: ErdColumn[];
  foreign_keys: ErdForeignKey[];
}

/** Full schema: table_name → table definition */
export type ErdSchema = Record<string, ErdTableSchema>;

export interface ErdNodePosition {
  x: number;
  y: number;
  collapsed: boolean;
}

/** Saved layout: table_name → position */
export type ErdLayout = Record<string, ErdNodePosition>;

export type RelType = "ONE_TO_ONE" | "ONE_TO_MANY" | "MANY_TO_MANY";
export type CascadeOp = "NO ACTION" | "RESTRICT" | "SET NULL" | "SET DEFAULT" | "CASCADE";

/** A user-defined / annotated relationship (stored in erd_relationships). */
export interface ErdRelationship {
  id: number;
  parent_table: string;
  child_table: string;
  foreign_key: string | null;
  rel_type: RelType;
  cascade_update: CascadeOp;
  cascade_delete: CascadeOp;
  label: string | null;
  notes: string | null;
}

export type ErdRelationshipCreate = Omit<ErdRelationship, "id">;
export type ErdRelationshipUpdate = Partial<ErdRelationshipCreate>;

/** The data payload stored on each React Flow table node.
 *  Extends Record<string, unknown> so React Flow v12 accepts it as node data. */
export interface ErdTableNodeData extends Record<string, unknown> {
  tableName: string;
  columns: ErdColumn[];
  collapsed: boolean;
}

/** Edge data: either a FK-derived edge or a user-defined relationship.
 *  Extends Record<string, unknown> so React Flow v12 accepts it as edge data. */
export interface ErdEdgeData extends Record<string, unknown> {
  source: "fk" | "user";
  rel_type: RelType;
  cascade_update?: string;
  cascade_delete?: string;
  label?: string | null;
  rel_id?: number;
  from_col?: string;
  to_col?: string;
  foreign_key?: string | null;
}

// ---------------------------------------------------------------------------
// Catalog group hierarchy types
// ---------------------------------------------------------------------------

export interface CatalogGroup {
  id: number;
  parent_group_id: number | null;
  group_name: string;
  group_code: string;
  description: string | null;
  display_order: number;
  is_active: boolean;
  linked_table: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type CatalogGroupCreate = Omit<CatalogGroup, "id" | "created_at" | "updated_at">;
export type CatalogGroupUpdate = Partial<CatalogGroupCreate>;

export interface CatalogGroupTree {
  id: number;
  group_name: string;
  group_code: string;
  description: string | null;
  display_order: number;
  is_active: boolean;
  linked_table: string | null;
  children: CatalogGroupTree[];
}

/** A generic item from any cat_* catalog table. */
export interface CatalogItem {
  id: number;
  catalog_group_id: number | null;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type CatalogItemCreate = Omit<CatalogItem, "id" | "created_at" | "updated_at">;
export type CatalogItemUpdate = Partial<CatalogItemCreate>;

// ---------------------------------------------------------------------------
// Row usage check (referential integrity guard)
// ---------------------------------------------------------------------------

export interface TableRef {
  table: string;
  column: string;
  count: number;
}

export interface UsageResult {
  table: string;
  id: number;
  references: TableRef[];
  total: number;
}

// ---------------------------------------------------------------------------
// Custom table schema types (catalog_column_defs + catalog_custom_rows)
// ---------------------------------------------------------------------------

export type CustomColType = "text" | "textarea" | "number" | "bool";

export interface ColumnDef {
  id: number;
  catalog_group_id: number;
  col_name: string;
  col_label: string;
  col_type: CustomColType;
  required: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export type ColumnDefCreate = Omit<ColumnDef, "id" | "catalog_group_id" | "created_at" | "updated_at">;
export type ColumnDefUpdate = Partial<ColumnDefCreate>;

export interface CustomRow {
  id: number;
  catalog_group_id: number;
  row_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/** The listing of one directory. */
export interface FsListing {
  path: string;
  parent: string | null;
  directories: FsEntry[];
  files: FsEntry[];
  drives: string[];
}
