# Integration / end-to-end tests

Reserved for tests that exercise more than one app together (e.g. web →
API), or full-stack scenarios once there is agent behavior worth testing
end-to-end.

Unit tests for the backend live in `apps/api/tests`. There is no frontend
unit test setup yet; add one (e.g. Vitest + React Testing Library) alongside
the first component that needs it.
