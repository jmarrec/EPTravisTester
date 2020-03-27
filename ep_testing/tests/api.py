import os
import stat
from tempfile import mkstemp
from subprocess import check_call, CalledProcessError  # , STDOUT

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
        st = os.stat(python_file_path)
        os.chmod(python_file_path, st.st_mode | stat.S_IEXEC)
        print(' [FILE WRITTEN] ', end='')
        # dev_null = open(os.devnull, 'w')
        try:
            check_call([python_file_path], env={'PYTHONPATH': install_root})  # , stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('Python API Wrapper Script failed!')
