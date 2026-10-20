# Compose troubleshooting

## Compose cannot start

- Confirm Docker Desktop is running on Windows/macOS, or the Docker Engine service is running on Linux. `docker compose version` should report the Compose plugin.
- Run commands from the repository root, where `compose.yaml` and `.env` are located.
- Copy `.env.example` to `.env`, set `KESTREL_DATA_DIR` to an absolute path, and create that directory before `docker compose up`.
- If Compose reports a mount or permission error, check that Docker can access the selected directory. On Linux/macOS set `KESTREL_UID`/`KESTREL_GID` to the directory owner IDs. Do not point the container at the source checkout.

## Port or readiness errors

Port 8080 must be available on the host; development mode also needs 5173. Stop an older native or Compose instance before retrying. `docker compose ps` and `docker compose logs kestrel` show service health and startup errors. The health check waits for `/api/v1/ready`; a container that is still starting is not ready to serve the UI.

If a build fails while downloading packages, retry after network access is restored. Runtime startup does not install dependencies. When dev dependencies change, recreate the dedicated caches with `docker compose -f compose.yaml -f compose.dev.yaml down -v` only if you accept deleting Compose's named development volumes; this does not delete `KESTREL_DATA_DIR`.

## Secret file cleanup

SSI secret export is optional plumbing and is not consumed by the current app. If a prepared file remains after interruption, stop Compose, inspect the path printed by `-prepare-ssi-compose-secret`, then run `-clean-ssi-compose-secret`. The export is plaintext on the host; cleanup is not secure erase. Do not paste the secret or its contents into issue reports or logs.
