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

export type ProcessExecutionStatus = "running" | "completed" | "failed" | "timeout" | "cancelled";

/** Response from `/api/v1/process/execute` and `/{id}/status` (see
 * `orbit_api.api.v1.process`). */
export interface ProcessStatusResponse {
  id: string;
  command: string[];
  cwd: string;
  status: ProcessExecutionStatus;
  pid: number | null;
  started_at: number;
  duration: number | null;
}

/** Response from `/api/v1/process/{id}/result`. */
export interface ProcessResultResponse extends ProcessStatusResponse {
  stdout: string;
  stderr: string;
  exit_code: number | null;
}

/** One match from `/api/v1/search`: a whole file (filename mode) or a line
 * within one (text/regex mode). */
export interface SearchMatch {
  path: string;
  line: number | null;
  column: number | null;
  text: string;
}

/** Response from `POST /api/v1/search` (see `orbit_api.api.v1.search`). */
export interface SearchResponse {
  query: string;
  mode: "filename" | "text" | "regex";
  matches: SearchMatch[];
  match_count: number;
  files_searched: number;
  search_duration: number;
}

/** Response from `GET /api/v1/search/index` and
 * `POST /api/v1/search/index/refresh`. */
export interface IndexStatusResponse {
  root: string;
  file_count: number;
  built_at: number | null;
  ignore_dirs: string[];
}

/** One commit, as returned by `GET /api/v1/git/log` (see
 * `orbit_api.api.v1.git`). */
export interface GitCommit {
  commit: string;
  short_commit: string;
  author_name: string;
  author_email: string;
  date: string;
  subject: string;
}

/** Response from `GET /api/v1/git/status`. */
export interface GitStatusResponse {
  staged: string[];
  modified: string[];
  untracked: string[];
  ignored: string[];
  clean: boolean;
}

/** Response from `GET /api/v1/git/branch`. */
export interface GitBranchResponse {
  branch: string | null;
  detached: boolean;
  head_commit: string | null;
}

/** Response from `GET /api/v1/git/log`. */
export interface GitLogResponse {
  commits: GitCommit[];
  count: number;
}

/** One file's line-change counts from `GET /api/v1/git/diff`. */
export interface GitDiffFile {
  path: string;
  added: number | null;
  removed: number | null;
  binary: boolean;
}

/** Response from `GET /api/v1/git/diff`. */
export interface GitDiffSummaryResponse {
  staged: boolean;
  files: GitDiffFile[];
  files_changed: number;
  total_added: number;
  total_removed: number;
}

/** Response from `GET /api/v1/git/metadata`. */
export interface GitMetadataResponse {
  root: string;
  branch: string | null;
  detached: boolean;
  head_commit: string | null;
  clean: boolean;
  remotes: Record<string, string>;
}

/** Minimal Git snapshot optionally included in Context Engine responses;
 * `null` when the workspace isn't a Git repository. */
export interface GitInfoResponse {
  branch: string | null;
  clean: boolean;
  modified_files: string[];
  recent_commits: string[];
}

/** Workspace identity as reported by the Context Engine. */
export interface ContextWorkspaceInfo {
  root: string;
  file_count: number;
  indexed_at: number | null;
}

/** File count/size for one extension, as reported by the Context Engine. */
export interface ExtensionBreakdownResponse {
  extension: string;
  file_count: number;
  total_size: number;
}

/** Response from `GET /api/v1/context/stats`. */
export interface ProjectStatsResponse {
  total_files: number;
  total_size: number;
  by_extension: ExtensionBreakdownResponse[];
}

/** Response from `GET /api/v1/context/summary`. */
export interface ProjectSummaryResponse {
  workspace: ContextWorkspaceInfo;
  stats: ProjectStatsResponse;
  git: GitInfoResponse | null;
}

/** One file gathered into a context bundle. */
export interface SelectedFileResponse {
  path: string;
  size: number;
  content: string | null;
  truncated: boolean;
}

/** Response from `POST /api/v1/context/generate`. */
export interface ContextBundleResponse {
  workspace: ContextWorkspaceInfo;
  stats: ProjectStatsResponse;
  files: SelectedFileResponse[];
  matches: SearchMatch[];
  query: string | null;
  generated_at: number;
  truncated: boolean;
  git: GitInfoResponse | null;
}

/** One registered provider, as returned by `GET /api/v1/providers`. */
export interface ProviderSummaryResponse {
  name: string;
  active: boolean;
}

/** One model available from a provider (`GET /api/v1/providers/models`). */
export interface ModelInfoResponse {
  name: string;
  size: number | null;
  modified_at: string | null;
}

/** Response from `GET /api/v1/providers/health`. */
export interface ProviderHealthResponse {
  healthy: boolean;
  provider: string;
  detail: string | null;
  checked_at: number;
}

/** Request body for `POST /api/v1/providers/generate`. */
export interface GenerateRequest {
  prompt: string;
  provider?: string;
  model?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  stop?: string[];
  context_query?: string;
  context_paths?: string[];
}

/** Response from `POST /api/v1/providers/generate`. */
export interface GenerateResponse {
  text: string;
  model: string;
  provider: string;
  duration: number;
}

