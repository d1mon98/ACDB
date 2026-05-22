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

/** Which database, if any, is currently connected. */
export interface ConnectionStatus {
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

/** The listing of one directory. */
export interface FsListing {
  path: string;
  parent: string | null;
  directories: FsEntry[];
  files: FsEntry[];
  drives: string[];
}
