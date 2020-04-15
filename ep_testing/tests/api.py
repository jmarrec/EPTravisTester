import os
import platform
from tempfile import mkdtemp, mkstemp
from subprocess import check_call, CalledProcessError, STDOUT

from ep_testing.exceptions import EPTestingException
from ep_testing.tests.base import BaseTest


class TestPythonAPIAccess(BaseTest):
    def name(self):
        return 'Test running an API script against pyenergyplus'

    @staticmethod
    def _api_script_content() -> str:
        return """
#!/usr/bin/env python3
from pyenergyplus.api import EnergyPlusAPI
api = EnergyPlusAPI()
glycol = api.functional.glycol(u"water")
for t in [5.0, 15.0, 25.0]:
    cp = glycol.specific_heat(t)
    rho = glycol.density(t)
        """

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        handle, python_file_path = mkstemp(suffix='.py')
        with os.fdopen(handle, 'w') as f:
            f.write(self._api_script_content())
        print(' [FILE WRITTEN] ', end='')
        dev_null = open(os.devnull, 'w')
        try:
            if platform.system() == 'Linux':
                py = 'python3'
            elif platform.system() == 'Darwin':
                py = '/usr/local/bin/python3'
            else:  # windows
                py = 'C:\\Python36\\Python.exe'
            my_env = os.environ.copy()
            my_env['PYTHONPATH'] = install_root
            if platform.system() == 'Windows':
                my_env['PATH'] = install_root + ';' + my_env['PATH']
            if self.verbose:
                check_call([py, python_file_path], env=my_env)
            else:
                check_call([py, python_file_path], env=my_env, stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('Python API Wrapper Script failed!')


def make_build_dir_and_build(cmake_build_dir: str, verbose: bool):
    try:
        os.makedirs(cmake_build_dir)
        my_env = os.environ.copy()
        if platform.system() == 'Darwin':  # my local comp didn't have cmake in path except in interact shells
            my_env["PATH"] = "/usr/local/bin:" + my_env["PATH"]
        command_line = [
            'cmake',
            '..'
        ]
        dev_null = open(os.devnull, 'w')
        if platform.system() == 'Windows':
            command_line.extend(['-G', 'Visual Studio 15 Win64'])
        if verbose:
            check_call(command_line, cwd=cmake_build_dir, env=my_env)
        else:
            check_call(command_line, cwd=cmake_build_dir, stdout=dev_null, stderr=STDOUT, env=my_env)
        command_line = [
            'cmake',
            '--build',
            '.'
        ]
        if platform.system() == 'Windows':
            command_line.extend(['--config', 'Release'])
        if verbose:
            check_call(command_line, env=my_env, cwd=cmake_build_dir)
        else:
            check_call(command_line, env=my_env, cwd=cmake_build_dir, stdout=dev_null, stderr=STDOUT)
        print(' [COMPILED] ', end='')
    except CalledProcessError:
        print("C API Wrapper Compilation Failed!")
        raise


class TestCAPIAccess(BaseTest):

    def __init__(self):
        super().__init__()
        self.source_file_name = 'func.c'
        self.target_name = 'TestCAPIAccess'

    def name(self):
        return 'Test running an API script against energyplus in C'

    def _api_cmakelists_content(self, install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = 'libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = 'libenergyplusapi.dylib'
        else:  # windows
            lib_file_name = 'energyplusapi.lib'
            install_path = install_path.replace('\\', '\\\\')
        return """
cmake_minimum_required(VERSION 3.10)
project({TARGET_NAME})
include_directories("{EPLUS_INSTALL_NO_SLASH}/include")
add_executable({TARGET_NAME} {SOURCE_FILE})
target_link_libraries({TARGET_NAME} "{EPLUS_INSTALL_NO_SLASH}/{LIB_FILE_NAME}")
        """.format(
            EPLUS_INSTALL_NO_SLASH=install_path, LIB_FILE_NAME=lib_file_name,
            TARGET_NAME=self.target_name, SOURCE_FILE=self.source_file_name
        )

    @staticmethod
    def _api_script_content() -> str:
        return """
#include <stddef.h>
#include <stdio.h>
#include <EnergyPlus/api/func.h>
int main() {
    initializeFunctionalAPI();
    Glycol glycol = NULL;
    glycol = glycolNew("WatEr");
    for (int temp=5; temp<35; temp+=10) {
        Real64 thisTemp = (float)temp;
        Real64 specificHeat = glycolSpecificHeat(glycol, thisTemp);
        printf("Cp = %8.3f\\n", specificHeat);
    }
    glycolDelete(glycol);
    printf("Hello, world!\\n");
}
        """

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        build_dir = mkdtemp()
        # print("Build dir set as: " + build_dir)
        c_file_name = self.source_file_name
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            f.write(self._api_script_content())
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content(install_root))
        print(' [CMAKE FILE WRITTEN] ', end='')
        dev_null = open(os.devnull, 'w')
        cmake_build_dir = os.path.join(build_dir, 'build')
        make_build_dir_and_build(cmake_build_dir, self.verbose)
        try:
            if platform.system() == 'Linux':
                # for Linux, we don't have to do anything, just run it
                new_binary_path = os.path.join(cmake_build_dir, self.target_name)
                command_line = [new_binary_path]
                if self.verbose:
                    check_call(command_line, cwd=install_root)
                else:
                    check_call(command_line, cwd=install_root, stdout=dev_null, stderr=STDOUT)
            elif platform.system() == 'Windows':
                # for Windows, we just need to make sure to append .exe
                new_binary_path = os.path.join(cmake_build_dir, 'Release', self.target_name + '.exe')
                print("Trying to run binary at: " + new_binary_path)
                command_line = [new_binary_path]
                if self.verbose:
                    check_call(command_line, cwd=install_root)
                else:
                    check_call(command_line, cwd=install_root, stdout=dev_null, stderr=STDOUT)
            elif platform.system() == 'Darwin':
                # for Mac, we can maybe do one of two things.
                # A: We can copy the new binary into the E+ install and run from there, or
                # B: We could potentially copy the Python DLL and E+ API DLL into the build dir and run from there, but
                #    that would be silly -- we wouldn't be expecting users to drag these resources around, so we won't
                #    demonstrate that here.
                built_binary_path = os.path.join(cmake_build_dir, self.target_name)
                new_binary_path = os.path.join(install_root, self.target_name)
                if self.verbose:
                    check_call(['cp', built_binary_path, new_binary_path])
                else:
                    check_call(['cp', built_binary_path, new_binary_path], stdout=dev_null, stderr=STDOUT)
                    command_line = [new_binary_path]
                    if self.verbose:
                        check_call(command_line, cwd=install_root)
                    else:
                        check_call(command_line, cwd=install_root, stdout=dev_null, stderr=STDOUT)
        except CalledProcessError:
            print('C API Wrapper Execution failed!')
            raise
        print(' [DONE]!')


class TestCppAPIDelayedAccess(BaseTest):

    def __init__(self):
        super().__init__()
        self.source_file_name = 'func.cpp'
        self.target_name = 'TestCAPIAccess'

    def name(self):
        return 'Test running an API script against energyplus in C++ but with delayed DLL loading'

    def _api_cmakelists_content(self) -> str:
        return """
cmake_minimum_required(VERSION 3.10)
project({TARGET_NAME})
add_executable({TARGET_NAME} {SOURCE_FILE})
target_link_libraries({TARGET_NAME} ${{CMAKE_DL_LIBS}})
        """.format(TARGET_NAME=self.target_name, SOURCE_FILE=self.source_file_name)

    @staticmethod
    def _api_script_content(install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = '/libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = '/libenergyplusapi.dylib'
        else:  # windows
            raise EPTestingException('Dont call TestCAPIDelayedAccess._api_script_content for Windows')
        return """
#include <iostream>
#include <dlfcn.h>
int main() {
    std::cout << "Opening eplus shared library...\\n";
    void* handle = dlopen("{EPLUS_INSTALL_NO_SLASH}{LIB_FILE_NAME}", RTLD_LAZY);
    if (!handle) {
        std::cerr << "Cannot open library: \\n";
        return 1;
    }
    dlerror(); // reset errors
    std::cout << "Loading init function symbol...\\n";
    typedef void (*init_t)();
    init_t init = (init_t) dlsym(handle, "initializeFunctionalAPI");
    const char *dlsym_error = dlerror();
    if (dlsym_error) {
        std::cerr << "Cannot load symbol 'initializeFunctionalAPI': \\n";
        dlclose(handle);
        return 1;
    }
    std::cout << "Calling to initialize...\\n";
    init();
    std::cout << "Closing library...\\n";
    dlclose(handle);
}
        """.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

    @staticmethod
    def _api_script_content_windows(install_path: str) -> str:
        lib_file_name = '\\\\energyplusapi.dll'
        install_path = install_path.replace('\\', '\\\\')
        return """
#include <windows.h>
#include <iostream>
int main() {
    std::cout << "Opening eplus shared library...\\n";
    HINSTANCE hInst;
    hInst = LoadLibrary("{EPLUS_INSTALL_NO_SLASH}{LIB_FILE_NAME}");
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
        """.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        build_dir = mkdtemp()
        # print("Build dir set as: " + build_dir)
        c_file_name = 'func.cpp'
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            if platform.system() == 'Linux' or platform.system() == 'Darwin':
                f.write(self._api_script_content(install_root))
            else:
                f.write(self._api_script_content_windows(install_root))
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content())
        print(' [CMAKE FILE WRITTEN] ', end='')
        dev_null = open(os.devnull, 'w')
        cmake_build_dir = os.path.join(build_dir, 'build')
        make_build_dir_and_build(cmake_build_dir, self.verbose)
        if platform.system() == 'Windows':
            # things get weird when running the program, clients need to understand DLL search paths on their platform
            # for Windows, the safe (default?) search path is:
            # 1. The directory from which the application loaded.
            # 2-4. System Directories -- not used
            # 5. The current directory.
            # 6. The directories that are listed in the PATH environment variable.
            # We will be trying to load the E+API DLL which depends on the python DLL and other Windows related DLL.
            # Thus we need to make sure that when we load the E+API DLL, Windows can find the Python DLL.  We can:
            # A: Copy the binary we built into the E+ install, so the DLL is found with (1) no matter the working dir
            # B: Change the working dir so that the DLLs are found with (5)
            # C: Set PATH to include the E+ install, so they are found with (6)
            # We can actually try all three
            # A: Copy the binary in and run it from back in the build dir
            built_binary_path = os.path.join(cmake_build_dir, 'Release', 'TestCAPIAccess')
            target_binary_path = os.path.join(install_root, 'TestCAPIAccess.exe')
            command_line = [target_binary_path]
            try:
                if self.verbose:
                    check_call(['cp', built_binary_path, target_binary_path])
                    check_call(command_line)
                else:
                    check_call(['cp', built_binary_path, target_binary_path], stdout=dev_null, stderr=STDOUT)
                    check_call(command_line, stdout=dev_null, stderr=STDOUT)
            except CalledProcessError:
                print('Delayed C API Wrapper Case A execution failed')
                raise
            print(' [CASE_A_SUCCESS] ', end='')
            os.remove(target_binary_path)  # clean out the copied binary to clean it all up
            # B: Change the working dir and run from ep install dir
            command_line = [built_binary_path]
            try:
                if self.verbose:
                    check_call(command_line, cwd=install_root)
                else:
                    check_call(command_line, cwd=install_root, stdout=dev_null, stderr=STDOUT)
            except CalledProcessError:
                print('Delayed C API Wrapper Case B execution failed')
                raise
            print(' [CASE_B_SUCCESS] ', end='')
            # C: Set Path to include e+ install
            command_line = [built_binary_path]
            try:
                my_env = os.environ.copy()
                my_env["PATH"] = install_root + ';' + my_env["PATH"]
                if self.verbose:
                    check_call(command_line, env=my_env)
                else:
                    check_call(command_line, env=my_env, stdout=dev_null, stderr=STDOUT)
            except CalledProcessError:
                print('Delayed C API Wrapper Case C execution failed')
                raise
            print(' [CASE_C_SUCCESS] ', end='')

        elif platform.system() == 'Darwin':
            # For Mac the situation is notably different.
            # The E+API DLL is adjusted so that it looks for the Python DLL at: @executable_path/Python
            # that means whatever executable is currently running must have the Python lib in the same directory
            # We have two options:
            # A: we can copy out the Python lib to the executable dir and run from anywhere
            # B: copy the executable into the E+ dir and run from anywhere
            # There shouldn't be any reason to change working directories in either case
            # We'll try both
            # A: copy Python lib into exec dir and run exec
            python_lib_path = os.path.join(install_root, 'Python')
            target_lib_path = os.path.join(cmake_build_dir, 'Python')
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
            command_line = [built_binary_path]
            try:
                if self.verbose:
                    check_call(['cp', python_lib_path, target_lib_path])
                    check_call(command_line)
                else:
                    check_call(['cp', python_lib_path, target_lib_path], stdout=dev_null, stderr=STDOUT)
                    check_call(command_line, stdout=dev_null, stderr=STDOUT)
                os.remove(target_lib_path)  # remove the copied lib so it is clean again
            except CalledProcessError:
                print("Delayed C API Wrapper Case A execution failed")
                raise
            print(' [CASE_A_SUCCESS] ', end='')
            # B: copy executable into E+ dir and run exec
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
            target_binary_path = os.path.join(install_root, 'TestCAPIAccess')
            command_line = [target_binary_path]
            try:
                if self.verbose:
                    check_call(['cp', built_binary_path, target_binary_path])
                    check_call(command_line)
                else:
                    check_call(['cp', built_binary_path, target_binary_path], stdout=dev_null, stderr=STDOUT)
                    check_call(command_line, stdout=dev_null, stderr=STDOUT)
            except CalledProcessError:
                print("Delayed C API Wrapper Case B execution failed")
                raise
            print(' [CASE_B_SUCCESS] ', end='')
        elif platform.system() == 'Linux':
            # Linux SO search paths are *basically*:
            # 1. directories listed in the LD_LIBRARY_PATH environment variable (DYLD_LIBRARY_PATH on OSX);
            # 2. directories listed in the executable's rpath;
            # 3. directories on the system search path
            # I found that the default library path will resolve to the current dir if not specified, at least in
            # elf/ld-load.c in the function fillin_rpath(...)
            # So I thought it would need to be in the working directory, but it seems to find it right next to the
            # executable no matter what.  Not sure.  Anyway, just test it by building and running it from the build
            # dir and we'll see what happens
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
            command_line = [built_binary_path]
            try:
                if self.verbose:
                    check_call(command_line)
                else:
                    check_call(command_line, stdout=dev_null, stderr=STDOUT)
            except CalledProcessError:
                print("Delayed C API Wrapper Case A execution failed")
                raise
            print(' [CASE_A_SUCCESS] ', end='')
        print(' [DONE]!')
