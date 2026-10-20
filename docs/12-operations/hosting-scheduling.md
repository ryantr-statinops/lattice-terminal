# Local runtime / Scheduling

No hosted runtime/cloud scheduler/telemetry. start.ps1 runs Go, which supervises Python and optional Vite development children. Built UI: localhost:8080; dev: localhost:5173. Python uses authenticated ephemeral loopback.

Installation needs toolchains/network; fixture runtime assets are local. Windows Job Objects own child trees; Stop must not leave workers. Listener reservation prevents another instance from opening/mutating active job state.

No actual SSI scheduler/transport enabled. Future requests require approved scope/quota/rights. News operating model remains independent. Closing browser doesn't stop services; use Stop explicitly.
