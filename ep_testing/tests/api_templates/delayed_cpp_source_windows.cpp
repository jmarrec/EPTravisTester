#include <windows.h>
#include <iostream>
int main() {
    std::cout << "Opening eplus shared library...\\n";
    HINSTANCE hInst;
    hInst = LoadLibraryEx("{EPLUS_INSTALL_NO_SLASH}{LIB_FILE_NAME}", NULL, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR);
    if (!hInst) {
        std::cerr << "Cannot open library: \\n";
        return 1;
    }
    typedef void (*INITFUNCTYPE)();
    INITFUNCTYPE init;
    init = (INITFUNCTYPE)GetProcAddress((HINSTANCE)hInst, "initializeFunctionalAPI");
    if (!init) {
        std::cerr << "Cannot get function \\n";
        return 1;
    }
    std::cout << "Calling to initialize\\n";
    init();
    std::cout << "Closing library\\n";
    FreeLibrary((HINSTANCE)hInst);
}