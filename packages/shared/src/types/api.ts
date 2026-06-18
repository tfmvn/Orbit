/**
 * Types mirroring the Orbit API's response shapes.
 *
 * These are intentionally kept in sync by hand for now. If the API surface
 * grows significantly, consider generating these from the API's OpenAPI
 * schema instead.
 */

export interface HealthResponse {
  status: "ok" | "degraded" | "down";
}

export interface VersionResponse {
  name: string;
  version: string;
  environment: "local" | "test" | "staging" | "production";
  git_commit: string | null;
}

export type TaskStatus =
  | "created"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface TaskResponse {
  id: string;
  name: string;
  status: TaskStatus;
  payload: Record<string, unknown>;
  result: unknown;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ToolMetadataResponse {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  version: string;
}

export interface ToolResultResponse {
  success: boolean;
  output: unknown;
  error: string | null;
  execution_time: number;
  metadata: Record<string, unknown>;
}

export interface WorkspaceInfoResponse {
  root: string;
  exists: boolean;
}

/** Shape of one entry returned by the filesystem tool's `list_directory`
 * and `metadata` operations (see `orbit_tools.filesystem.FilesystemTool`). */
export interface FilesystemEntry {
  name: string;
  path: string;
  is_file: boolean;
  is_dir: boolean;
  size: number;
  modified: number;
  mode: string;
}
