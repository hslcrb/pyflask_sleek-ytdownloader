/* Start the bundled app from Explorer or a terminal, without using cmd.exe. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <wchar.h>

enum { PATH_CAP = 32768, COMMAND_CAP = 32768 };

static wchar_t directory[PATH_CAP], python[PATH_CAP], script[PATH_CAP];
static wchar_t command[COMMAND_CAP];

static int fail(const wchar_t *message, DWORD code) {
    fwprintf(stderr, L"Sleek: %ls (Windows error %lu)\n", message, (unsigned long)code);
    MessageBoxW(NULL, message, L"Sleek Downloader", MB_OK | MB_ICONERROR);
    return 1;
}

static BOOL WINAPI wait_for_python(DWORD event) {
    // The Python child shares the console and receives Ctrl+C independently.
    return event == CTRL_C_EVENT || event == CTRL_BREAK_EVENT;
}

int wmain(int argc, wchar_t **argv) {
    const BOOL smoke = argc == 2 && wcscmp(argv[1], L"--smoke-test") == 0;
    if (argc > 1 && !smoke) {
        fwprintf(stderr, L"Usage: SleekDownloader.exe [--smoke-test]\n");
        return 2;
    }

    DWORD length = GetModuleFileNameW(NULL, directory, PATH_CAP);
    if (length == 0 || length >= PATH_CAP) {
        return fail(L"Could not locate the Sleek installation.", GetLastError());
    }
    wchar_t *slash = wcsrchr(directory, L'\\');
    if (slash == NULL) return fail(L"Invalid Sleek installation path.", ERROR_INVALID_NAME);
    *slash = L'\0';

    if (swprintf(python, PATH_CAP, L"%ls\\runtime\\python.exe", directory) < 0 ||
        swprintf(script, PATH_CAP, L"%ls\\app\\launch.py", directory) < 0 ||
        swprintf(command, COMMAND_CAP, L"\"%ls\" \"%ls\"%ls", python, script,
                 smoke ? L" --smoke-test" : L"") < 0) {
        return fail(L"The Sleek installation path is too long.", ERROR_FILENAME_EXCED_RANGE);
    }

    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION child = {0};
    startup.cb = sizeof(startup);
    SetConsoleCtrlHandler(wait_for_python, TRUE);
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, 0, NULL,
                        directory, &startup, &child)) {
        return fail(L"Could not start the bundled runtime. Extract or reinstall all files.",
                    GetLastError());
    }
    CloseHandle(child.hThread);
    DWORD code = 1;
    if (WaitForSingleObject(child.hProcess, INFINITE) == WAIT_OBJECT_0) {
        GetExitCodeProcess(child.hProcess, &code);
    }
    CloseHandle(child.hProcess);
    if (code != 0 && !smoke) {
        MessageBoxW(NULL, L"Sleek exited with an error. Check port 5000 and try again.",
                    L"Sleek Downloader", MB_OK | MB_ICONERROR);
    }
    return (int)code;
}
