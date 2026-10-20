# One local account

The repository `.env` is the authoritative source for the local username and
password. Restart after editing it. Credentials are never returned to the UI,
logged, backed up, or stored in profile.json. SSI stays in the OS keyring.

The default data directory is repository `data/`, containing kestrel.sqlite and
the existing workspace/artifact directories. No fixture profile is imported.
Explicit -data overrides are reserved for isolated runs.

Implementation uses small commits on main, without pushing. After the clean
runtime passes acceptance, remove only .cache/visual-acceptance-20261020 and
the external kestrel-ui-review/profile created for the UI review. Keep build
artifacts and tool caches. Do not stop active jobs to perform this cleanup.

Users enter their own password in .env; no default password is supplied.
