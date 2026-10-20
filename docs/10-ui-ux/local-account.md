# One local account

The repository `.env` is the authoritative source for the local username and
password. Restart after editing it. Credentials are never returned to the UI,
logged, backed up, or stored in profile.json. SSI stays in the OS keyring.

The default data directory is repository `data/`, containing kestrel.sqlite and
the existing workspace/artifact directories. Static fixture inputs remain in
their tracked locations; no fixture profile/database is imported. Explicit
`-data` overrides are reserved for isolated runs.

Implementation uses small commits on main, without pushing. After verifying
both old runtimes had stopped and no jobs were active, remove only
`.cache/visual-acceptance-20261020` and the external
`kestrel-ui-review/profile` created for the UI review. Keep build artifacts
and tool caches.

Users enter their own password in .env; no default password is supplied.
The gateway derives an Argon2id verifier at startup and holds it only in
memory. The browser never sets up or resets the password; edit .env and restart.
SSI credentials remain in the OS keyring. Backups contain only allowlisted
application data and restore under the credentials currently in .env.
