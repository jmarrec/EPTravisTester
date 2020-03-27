import os

from ep_testing.tests.idf_runner import TestPlainDDRunEPlusFile
from ep_testing.tests.transition import TransitionOldFile


class Tester:

    def __init__(self, install_path: str, last_version_tag: str):
        self.install_path = install_path
        self.last_version = last_version_tag

    def run(self):
        saved_path = os.getcwd()
        os.chdir(self.install_path)
        try:
            TestPlainDDRunEPlusFile().run(self.install_path, {'test_file': '1ZoneUncontrolled.idf'})
            TestPlainDDRunEPlusFile().run(self.install_path, {'test_file': 'PythonPluginCustomOutputVariable.idf'})
            TransitionOldFile().run(self.install_path, {'last_version': self.last_version})
        except Exception:
            raise
        finally:
            os.chdir(saved_path)
