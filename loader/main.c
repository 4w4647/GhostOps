#include <windows.h>
#include <string.h>

#ifndef BEACON_DLL
#define BEACON_DLL "beacon.dll"
#endif

int WINAPI WinMain(HINSTANCE h, HINSTANCE p, LPSTR cmd, int show) {
    (void)h; (void)p; (void)cmd; (void)show;

    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    char *sep = strrchr(path, '\\');
    if (sep) *(sep + 1) = '\0';
    else     path[0]   = '\0';
    strncat(path, BEACON_DLL, MAX_PATH - strlen(path) - 1);

    HMODULE mod = LoadLibraryA(path);
    if (!mod) return 1;

    FARPROC fn = GetProcAddress(mod, "BeaconMain");
    if (!fn) { FreeLibrary(mod); return 1; }

    ((void (WINAPI *)(void))fn)();
    return 0;
}
