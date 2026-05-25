// Thin REST client for the backend API.
//
// All requests use relative /api URLs; in development the Vite dev server
// proxies them to the FastAPI backend (see vite.config.ts).

import type {
  CatalogGroup,
  CatalogGroupCreate,
  CatalogGroupUpdate,
  CatalogGroupTree,
  CatalogItem,
  CatalogItemCreate,
  CatalogItemUpdate,
  ColumnDef,
  ColumnDefCreate,
  ColumnDefUpdate,
  CustomRow,
  UsageResult,
  ConnectionStatus,
  DatabaseInfo,
  DatabaseListResponse,
  ErdLayout,
  ErdRelationship,
  ErdRelationshipCreate,
  ErdRelationshipUpdate,
  ErdSchema,
  FsListing,
  ListResponse,
  Row,
} from "./types";

const BASE = "/api";

/** Turn a FastAPI error `detail` (string, or 422 validation array) into text. */
function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => (d && d.msg ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (detail == null) return "Request failed.";
  return JSON.stringify(detail);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(BASE + path, {
    method,
    headers:
      body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* error response had no JSON body */
    }
    throw new Error(formatDetail(detail));
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function query(params?: Record<string, unknown>): string {
  if (!params) return "";
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  return parts.length ? `?${parts.join("&")}` : "";
}

/** Build a CRUD client for one of the database-management surfaces (catalog,
 *  project, or the legacy /databases alias).  All three share the same shape. */
function makeDbClient(prefix: string) {
  return {
    list: () => request<DatabaseListResponse>("GET", prefix),
    status: () => request<ConnectionStatus>("GET", `${prefix}/status`),
    create: (name: string) =>
      request<DatabaseInfo>("POST", prefix, { name }),
    connect: (name: string) =>
      request<ConnectionStatus>(
        "POST",
        `${prefix}/${encodeURIComponent(name)}/connect`,
      ),
    open: (path: string) =>
      request<ConnectionStatus>("POST", `${prefix}/open`, { path }),
    disconnect: () =>
      request<ConnectionStatus>("POST", `${prefix}/disconnect`),
    rename: (name: string, newName: string) =>
      request<DatabaseInfo>("PUT", `${prefix}/${encodeURIComponent(name)}`, {
        new_name: newName,
      }),
    remove: (name: string) =>
      request<void>("DELETE", `${prefix}/${encodeURIComponent(name)}`),
  };
}

export const api = {
  list: (slug: string, params?: Record<string, unknown>) =>
    request<ListResponse>("GET", `/${slug}${query(params)}`),

  activateProject: (id: number) =>
    request<ConnectionStatus>("POST", `/projects/${id}/activate`),

  /** Merged view -- project rows with their catalog records joined in. */
  listMerged: (slug: string, params?: Record<string, unknown>) =>
    request<ListResponse>("GET", `/${slug}/merged${query(params)}`),

  create: (slug: string, body: Row) => request<Row>("POST", `/${slug}`, body),

  update: (slug: string, id: number, body: Row) =>
    request<Row>("PUT", `/${slug}/${id}`, body),

  remove: (slug: string, id: number) =>
    request<void>("DELETE", `/${slug}/${id}`),

  dashboard: (projectId: number) =>
    request<Row>("GET", `/projects/${projectId}/dashboard`),

  /** Download a table as CSV text. */
  exportCsv: async (
    slug: string,
    params?: Record<string, unknown>,
  ): Promise<string> => {
    const res = await fetch(`${BASE}/${slug}/export-csv${query(params)}`);
    if (!res.ok) throw new Error(`Export failed (${res.status}).`);
    return res.text();
  },

  /** Import rows from CSV text; returns { created, errors }. */
  importCsv: (
    slug: string,
    content: string,
    params?: Record<string, unknown>,
  ) =>
    request<{ created: number; errors: { row: number; error: string }[] }>(
      "POST",
      `/${slug}/import-csv${query(params)}`,
      { content },
    ),

  // Database Browser -- catalog (system reference data) and project (per-project
  // electrical data) databases are managed separately.  Each role has its own
  // CRUD surface under /api/catalog-databases or /api/project-databases.
  catalogDatabases: makeDbClient("/catalog-databases"),
  projectDatabases: makeDbClient("/project-databases"),
  /** Combined status of both connections (used by the app header). */
  dbStatus: () =>
    request<{ catalog: ConnectionStatus; project: ConnectionStatus }>(
      "GET",
      "/db-status",
    ),
  /** Backward-compat alias: pre-split UI talked to /api/databases. */
  databases: makeDbClient("/databases"),

  // Filesystem browse -- backs the Database Browser's file picker.
  fs: {
    browse: (path?: string) =>
      request<FsListing>(
        "GET",
        `/fs/browse${path ? `?path=${encodeURIComponent(path)}` : ""}`,
      ),
  },

  // Catalog Groups -- hierarchical group tree + CRUD.
  catalogGroups: {
    tree: () => request<CatalogGroupTree[]>("GET", "/catalog-groups/tree"),
    list: () => request<ListResponse<CatalogGroup>>("GET", "/catalog-groups"),
    get: (id: number) => request<CatalogGroup>("GET", `/catalog-groups/${id}`),
    create: (body: CatalogGroupCreate) =>
      request<CatalogGroup>("POST", "/catalog-groups", body),
    update: (id: number, body: CatalogGroupUpdate) =>
      request<CatalogGroup>("PUT", `/catalog-groups/${id}`, body),
    remove: (id: number) => request<void>("DELETE", `/catalog-groups/${id}`),
  },

  // Catalog Items -- generic items in a cat_* table, filtered by group.
  catalogItems: {
    list: (slug: string, groupId?: number) =>
      request<ListResponse<CatalogItem>>(
        "GET",
        `/${slug}${groupId != null ? `?catalog_group_id=${groupId}` : ""}`,
      ),
    create: (slug: string, body: CatalogItemCreate) =>
      request<CatalogItem>("POST", `/${slug}`, body),
    update: (slug: string, id: number, body: CatalogItemUpdate) =>
      request<CatalogItem>("PUT", `/${slug}/${id}`, body),
    remove: (slug: string, id: number) =>
      request<void>("DELETE", `/${slug}/${id}`),
  },

  // Usage check -- tells the UI which rows reference a given catalog row.
  checkUsage: (tableName: string, rowId: number) =>
    request<UsageResult>("GET", `/usage-check/${tableName}/${rowId}`),

  // Custom table schema (column defs + data rows for user-created groups).
  customTable: {
    listColumns: (groupId: number) =>
      request<ColumnDef[]>("GET", `/catalog-groups/${groupId}/columns`),
    createColumn: (groupId: number, body: ColumnDefCreate) =>
      request<ColumnDef>("POST", `/catalog-groups/${groupId}/columns`, body),
    updateColumn: (groupId: number, colId: number, body: ColumnDefUpdate) =>
      request<ColumnDef>("PUT", `/catalog-groups/${groupId}/columns/${colId}`, body),
    deleteColumn: (groupId: number, colId: number) =>
      request<void>("DELETE", `/catalog-groups/${groupId}/columns/${colId}`),
    listRows: (groupId: number) =>
      request<CustomRow[]>("GET", `/catalog-groups/${groupId}/rows`),
    createRow: (groupId: number, data: Record<string, unknown>) =>
      request<CustomRow>("POST", `/catalog-groups/${groupId}/rows`, { row_data: data }),
    updateRow: (groupId: number, rowId: number, data: Record<string, unknown>) =>
      request<CustomRow>("PUT", `/catalog-groups/${groupId}/rows/${rowId}`, { row_data: data }),
    deleteRow: (groupId: number, rowId: number) =>
      request<void>("DELETE", `/catalog-groups/${groupId}/rows/${rowId}`),
  },

  // ERD -- schema introspection, layout persistence, relationship CRUD.
  erd: {
    schema: () => request<ErdSchema>("GET", "/erd/schema"),

    getLayout: () => request<ErdLayout>("GET", "/erd/layout"),

    saveLayout: (positions: ErdLayout) =>
      request<{ saved: number }>("PUT", "/erd/layout", { positions }),

    listRelationships: () =>
      request<ErdRelationship[]>("GET", "/erd/relationships"),

    createRelationship: (body: ErdRelationshipCreate) =>
      request<ErdRelationship>("POST", "/erd/relationships", body),

    updateRelationship: (id: number, body: ErdRelationshipUpdate) =>
      request<ErdRelationship>("PUT", `/erd/relationships/${id}`, body),

    deleteRelationship: (id: number) =>
      request<void>("DELETE", `/erd/relationships/${id}`),
  },
};
