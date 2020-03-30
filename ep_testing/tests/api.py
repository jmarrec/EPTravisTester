import os
import platform
from tempfile import mkdtemp, mkstemp
from subprocess import check_call, check_output, CalledProcessError, STDOUT

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

    def run(self, install_root: str, kwargs: dict):
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        handle, python_file_path = mkstemp(suffix='.py')
        with os.fdopen(handle, 'w') as f:
            f.write(self._api_script_content())
        print(' [FILE WRITTEN] ', end='')
        # dev_null = open(os.devnull, 'w')
        try:
            if platform.system() == 'Linux':
                py = 'python3'
            elif platform.system() == 'Darwin':
                py = '/usr/local/bin/python3'
            else:  # windows
                py = '/c/Python36/python.exe'
                print(check_output(['which', 'python.exe']))
            check_call([py, python_file_path], env={'PYTHONPATH': install_root})  # , stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('Python API Wrapper Script failed!')


class TestCAPIAccess(BaseTest):
    Verbose = True

    def name(self):
        return 'Test running an API script against energyplus in C'

    @staticmethod
    def _api_cmakelists_content(install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = 'libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = 'libenergyplusapi.dylib'
        else:  # windows
            lib_file_name = 'energyplusapi.dll'
            install_path = install_path.replace('\\', '/')
        return """
cmake_minimum_required(VERSION 3.10)
project(TestCAPIAccess)
include_directories("{EPLUS_INSTALL_NO_SLASH}/include")
add_executable(TestCAPIAccess func.c)
target_link_libraries(TestCAPIAccess "{EPLUS_INSTALL_NO_SLASH}/{LIB_FILE_NAME}")
        """.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

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

    def run(self, install_root: str, kwargs: dict):
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        build_dir = mkdtemp()
        # print("Build dir set as: " + build_dir)
        c_file_name = 'func.c'
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            f.write(self._api_script_content())
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content(install_root))
        print(' [CMAKE FILE WRITTEN] ', end='')
        dev_null = open(os.devnull, 'w')
        saved_dir = os.getcwd()
        os.chdir(build_dir)
        cmake_build_dir = os.path.join(build_dir, 'build')
        try:
            os.makedirs(cmake_build_dir)
            os.chdir(cmake_build_dir)
            my_env = os.environ.copy()
            if platform.system() == 'Darwin':  # my local comp didn't have cmake in path except in interact shells
                my_env["PATH"] = "/usr/local/bin:" + my_env["PATH"]
            command_line = [
                'cmake',
                '..'
            ]
            if platform.system() == 'Windows':
                command_line.extend(['-G', 'Visual Studio 15 Win64'])
            if self.Verbose:
                check_call(command_line, env=my_env)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT, env=my_env)
            command_line = [
                'cmake',
                '--build',
                '.',
                '-j',
                '2'
            ]
            if platform.system() == 'Windows':
                command_line.extend(['--config', 'Release'])
            if self.Verbose:
                check_call(command_line)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [COMPILED] ', end='')
        except CalledProcessError:
            print("C API Wrapper Compilation Failed!")
            raise
        # here is where it is limited -- we have to run from the e+ install dir
        try:
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
            target_binary_path = os.path.join(install_root, 'TestCAPIAccess')
            if platform.system() == 'Windows':
                built_binary_path += '.exe'
                target_binary_path += '.exe'
            if self.Verbose:
                check_call(['cp', built_binary_path, target_binary_path])
            else:
                check_call(['cp', built_binary_path, target_binary_path], stdout=dev_null, stderr=STDOUT)
            command_line = [target_binary_path]
            os.chdir(install_root)
            if self.Verbose:
                check_call(command_line)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            print('C API Wrapper Execution failed!')
            raise
        os.chdir(saved_dir)


class TestCAPIDelayedAccess(BaseTest):
    Verbose = True

    def name(self):
        return 'Test running an API script against energyplus in C but with delayed DLL loading'

    @staticmethod
    def _api_cmakelists_content() -> str:
        return """
cmake_minimum_required(VERSION 3.10)
project(TestCAPIAccess)
add_executable(TestCAPIAccess func.cc)
target_link_libraries(TestCAPIAccess ${CMAKE_DL_LIBS})
        """

    @staticmethod
    def _api_script_content(install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = '/libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = '/libenergyplusapi.dylib'
        else:  # windows
            lib_file_name = '\\energyplusapi.dll'
            install_path = install_path.replace('\\', '\\\\')
        return """
#include <iostream>
#include <dlfcn.h>
int main() {
    std::cout << "Opening eplus shared library...\\n";
    void* handle = dlopen("{EPLUS_INSTALL_NO_SLASH}{LIB_FILE_NAME}", RTLD_LAZY);
    if (!handle) {
        std::cerr << "Cannot open library: " << dlerror() << '\\n';
        return 1;
    }
    dlerror(); // reset errors
    std::cout << "Loading init function symbol...\\n";
    typedef void (*init_t)();
    init_t init = (init_t) dlsym(handle, "initializeFunctionalAPI");
    const char *dlsym_error = dlerror();
    if (dlsym_error) {
        std::cerr << "Cannot load symbol 'hello': " << dlsym_error << '\\n';
        dlclose(handle);
        return 1;
    }
    std::cout << "Calling to initialize...\\n";
    init();
    std::cout << "Closing library...\\n";
    dlclose(handle);
}
        """.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

    def run(self, install_root: str, kwargs: dict):
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        build_dir = mkdtemp()
        # print("Build dir set as: " + build_dir)
        c_file_name = 'func.cc'
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            f.write(self._api_script_content(install_root))
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content())
        print(' [CMAKE FILE WRITTEN] ', end='')
        dev_null = open(os.devnull, 'w')
        saved_dir = os.getcwd()
        os.chdir(build_dir)
        cmake_build_dir = os.path.join(build_dir, 'build')
        try:
            os.makedirs(cmake_build_dir)
            os.chdir(cmake_build_dir)
            my_env = os.environ.copy()
            if platform.system() == 'Darwin':  # my local comp didn't have cmake in path except in interact shells
                my_env["PATH"] = "/usr/local/bin:" + my_env["PATH"]
            command_line = [
                'cmake',
                '..'
            ]
            if platform.system() == 'Windows':
                command_line.extend(['-G', 'Visual Studio 15 Win64'])
            if self.Verbose:
                check_call(command_line, env=my_env)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT, env=my_env)
            print(" [CONFIGURED] ", end='')
            command_line = [
                'cmake',
                '--build',
                '.',
                '-j',
                '2'
            ]
            if platform.system() == 'Windows':
                command_line.extend(['--config', 'Release'])
            if self.Verbose:
                check_call(command_line)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [COMPILED] ', end='')
        except CalledProcessError:
            print("C API Wrapper Compilation Failed!")
            raise
        # here is where it is limited -- we have to run from the e+ install dir
        try:
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
            target_binary_path = os.path.join(install_root, 'TestCAPIAccess')
            if platform.system() == 'Windows':
                built_binary_path += '.exe'
                target_binary_path += '.exe'
            if self.Verbose:
                check_call(['cp', built_binary_path, target_binary_path])
            else:
                check_call(['cp', built_binary_path, target_binary_path], stdout=dev_null, stderr=STDOUT)
            command_line = [target_binary_path]
            os.chdir(install_root)
            if self.Verbose:
                check_call(command_line)
            else:
                check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            print('C API Wrapper Execution failed!')
            raise
        os.chdir(saved_dir)
