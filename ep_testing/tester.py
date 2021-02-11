import os
from tempfile import mkdtemp

from ep_testing.config import TestConfiguration, OS
from ep_testing.tests.api import TestPythonAPIAccess, TestCAPIAccess, TestCppAPIDelayedAccess
from ep_testing.tests.energyplus import TestPlainDDRunEPlusFile
from ep_testing.tests.expand_objects import TestExpandObjectsAndRun
from ep_testing.tests.transition import TransitionOldFile


class Tester:

    def __init__(self, config: TestConfiguration, install_path: str, verbose: bool):
        self.install_path = install_path
        self.config = config
        self.verbose = verbose

    def run(self):
        saved_path = os.getcwd()
        temp_dir = mkdtemp()
        print('Creating sandbox dir and changing to it: ' + temp_dir)
        os.chdir(temp_dir)
        TestPlainDDRunEPlusFile().run(
            self.install_path, self.verbose, {'test_file': '1ZoneUncontrolled.idf'}
        )
        TestPlainDDRunEPlusFile().run(
            self.install_path, self.verbose, {'test_file': 'PythonPluginCustomOutputVariable.idf'}
        )
        TestExpandObjectsAndRun().run(
            self.install_path, self.verbose, {'test_file': 'HVACTemplate-5ZoneFanCoil.idf'}
        )
        allow_failure = False
        if self.config.last_version == self.config.this_version:
            print("Last version in the same as this version, allowing "
                  "Transition test to fail.")
            allow_failure = True
        TransitionOldFile().run(
            self.install_path, self.verbose,
            {
                'last_version': self.config.tag_last_version,
                'allow_failure': allow_failure
            }
        )
        if self.config.os == OS.Windows:
            print("Windows Symlink runs are not testable on Travis, I think the user needs symlink privilege.")
        else:
            TestPlainDDRunEPlusFile().run(
                self.install_path, self.verbose, {'test_file': '1ZoneUncontrolled.idf', 'binary_sym_link': True}
            )
        TestCAPIAccess().run(
            self.install_path, self.verbose, {'os': self.config.os, 'bitness': self.config.bitness}
        )
        TestCppAPIDelayedAccess().run(
            self.install_path, self.verbose, {'os': self.config.os, 'bitness': self.config.bitness}
        )
        if self.config.bitness == 'x32':
            print("Travis does not have a 32-bit Python package readily available, so not testing Python API")
        elif self.config.os == OS.Mac and self.config.os_version == '10.14':
            print("E+ technically supports 10.15, but most things work on 10.14. Not Python API though, skipping that.")
        else:
            TestPythonAPIAccess().run(
                self.install_path, self.verbose, {'os': self.config.os}
            )
        os.chdir(saved_path)
