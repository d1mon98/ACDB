// Thin REST client for the backend API.
//
// All requests use relative /api URLs; in development the Vite dev server
// proxies them to the FastAPI backend (see vite.config.ts).

import type {
  ConnectionStatus,
  DatabaseInfo,
  DatabaseListResponse,
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

export const api = {
  list: (slug: string, params?: Record<string, unknown>) =>
    request<ListResponse>("GET", `/${slug}${query(params)}`),

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

  // Database Browser -- manage the database files and the active connection.
  databases: {
    list: () => request<DatabaseListResponse>("GET", "/databases"),
    status: () => request<ConnectionStatus>("GET", "/databases/status"),
    create: (name: string) =>
      request<DatabaseInfo>("POST", "/databases", { name }),
    connect: (name: string) =>
      request<ConnectionStatus>(
        "POST",
        `/databases/${encodeURIComponent(name)}/connect`,
      ),
    /** Connect to a database file at an arbitrary filesystem path. */
    open: (path: string) =>
      request<ConnectionStatus>("POST", "/databases/open", { path }),
    disconnect: () =>
      request<ConnectionStatus>("POST", "/databases/disconnect"),
    rename: (name: string, newName: string) =>
      request<DatabaseInfo>("PUT", `/databases/${encodeURIComponent(name)}`, {
        new_name: newName,
      }),
    remove: (name: string) =>
      request<void>("DELETE", `/databases/${encodeURIComponent(name)}`),
  },

  // Filesystem browse -- backs the Database Browser's file picker.
  fs: {
    browse: (path?: string) =>
      request<FsListing>(
        "GET",
        `/fs/browse${path ? `?path=${encodeURIComponent(path)}` : ""}`,
      ),
  },
};
