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
