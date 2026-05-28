# docker

`docker-compose.yml` builds and runs both apps together for local
development or demos. It expects `apps/api/.env` and `apps/web/.env` to
exist — copy them from the `.env.example` files first:

```bash
cp ../apps/api/.env.example ../apps/api/.env
cp ../apps/web/.env.example ../apps/web/.env
```

Then, from the repo root:

```bash
make docker-up
# or: docker compose -f docker/docker-compose.yml up --build
```

- API: http://localhost:8000
- Web: http://localhost:3000

Each app also has its own standalone `Dockerfile` (`apps/api/Dockerfile`,
`apps/web/Dockerfile`) that can be built independently; the web image's
build context is the repo root since it depends on the `@orbit/shared`
workspace package.
