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
        if platform.system() != 'Linux':
            print("SKIPPING PYTHON API TEST")
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

    def name(self):
        return 'Test running an API script against energyplus in C'

    @staticmethod
    def _api_cmakelists_content(install_path: str) -> str:
        return """
cmake_minimum_required(VERSION 3.10)
project(TestCAPIAccess)
include_directories("{EPLUS_INSTALL_NO_SLASH}/include")
add_executable(TestCAPIAccess func.c)
target_link_libraries(TestCAPIAccess "{EPLUS_INSTALL_NO_SLASH}/libenergyplusapi.so")
        """.replace('{EPLUS_INSTALL_NO_SLASH}', install_path)

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
    }
    glycolDelete(glycol);
    printf("Hello, world!\\n");
}
        """

    def run(self, install_root: str, kwargs: dict):
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        build_dir = mkdtemp()
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
        try:
            if platform.system() == 'Linux' or platform.system() == 'Darwin':
                cmake_build_dir = os.path.join(build_dir, 'build')
                os.makedirs(cmake_build_dir)
                os.chdir(cmake_build_dir)
                command_line = [
                    'cmake',
                    '..'
                ]
                check_call(command_line, stdout=dev_null, stderr=STDOUT)
                command_line = [
                    'make',
                    '-j2'
                ]
            else:  # windows
                command_line = []
            check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [COMPILED] ', end='')
        except CalledProcessError:
            raise EPTestingException('C API Wrapper Compilation failed!')
        try:
            if platform.system() == 'Linux' or platform.system() == 'Darwin':
                command_line = ['./build/TestCAPIAccess']
            else:  # windows
                command_line = []
            check_call(command_line, stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('C API Wrapper Execution failed!')
        os.chdir(saved_dir)
