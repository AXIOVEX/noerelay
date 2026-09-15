# Docker project

`compose.yml` is the deployment definition. Dockerfiles, LiteLLM provider mappings, WebUI initialization, branding, and redacted container configuration belong here. The A2A Dockerfile is `a2a.Dockerfile`; its build context remains `services/a2a-adapter`.

The repository-root `docker-compose.yml` includes this definition with the repository as its build/mount context. Existing commands continue to work:

```powershell
docker compose --env-file .env.docker config --quiet
docker compose --env-file .env.docker build noerelay
docker compose --env-file .env.docker up -d
```

`.env.docker` remains a local, ignored configuration file at the repository root. Data volumes and credentials are not build artifacts. Use `deploy/host/local-stack.ps1` to manage both Docker and host inference together.
