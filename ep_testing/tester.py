import os

from ep_testing.config import TestConfiguration
from ep_testing.tests.idf_runner import TestPlainDDRunEPlusFile
from ep_testing.tests.transition import TransitionOldFile


class Tester:

    def __init__(self, config: TestConfiguration, install_path: str):
        self.install_path = install_path
        self.last_version = config.TAG_LAST_VERSION

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
