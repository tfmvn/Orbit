# scripts

Small helper scripts used by the `Makefile` and CI. They're plain bash so
they're easy to read and run directly (`./scripts/dev.sh`) without needing
`make`.

- `setup.sh` — install backend and frontend dependencies
- `dev.sh` — run the API and web app concurrently
- `lint.sh` — run all linters/formatters in check mode
- `format.sh` — auto-format Python and TypeScript
