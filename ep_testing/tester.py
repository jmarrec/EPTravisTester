import os
from platform import system

from ep_testing.config import TestConfiguration
from ep_testing.tests.api import TestPythonAPIAccess, TestCAPIAccess
from ep_testing.tests.documentation import TestVersionInfoInDocumentation
from ep_testing.tests.energyplus import TestPlainDDRunEPlusFile
from ep_testing.tests.expand_objects import TestExpandObjectsAndRun
from ep_testing.tests.transition import TransitionOldFile


class Tester:

    def __init__(self, config: TestConfiguration, install_path: str):
        self.install_path = install_path
        self.config = config

    def run(self):
        saved_path = os.getcwd()
        os.chdir(self.install_path)
        try:
            TestPlainDDRunEPlusFile().run(
                self.install_path, {'test_file': '1ZoneUncontrolled.idf'}
            )
            TestPlainDDRunEPlusFile().run(
                self.install_path, {'test_file': 'PythonPluginCustomOutputVariable.idf'}
            )
            TestExpandObjectsAndRun().run(
                self.install_path, {'test_file': 'HVACTemplate-5ZoneFanCoil.idf'}
            )
            TransitionOldFile().run(
                self.install_path, {'last_version': self.config.TAG_LAST_VERSION}
            )
            if system() == 'Linux':
                TestVersionInfoInDocumentation().run(
                    self.install_path, {'pdf_file': 'AuxiliaryPrograms.pdf', 'version_string': self.config.THIS_VERSION}
                )
                TestPythonAPIAccess().run(
                    self.install_path, {}
                )
                TestCAPIAccess().run(
                    self.install_path, {}
                )
            else:
                print("Skipping API and Doc stuff on Linux FOR NOW!!!!")
        except Exception:
            raise
        finally:
            os.chdir(saved_path)
