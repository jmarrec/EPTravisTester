import os
from platform import system
from tempfile import mkdtemp

from ep_testing.config import TestConfiguration
from ep_testing.tests.api import TestPythonAPIAccess, TestCAPIAccess, TestCppAPIDelayedAccess
from ep_testing.tests.documentation import TestVersionInfoInDocumentation
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
        TransitionOldFile().run(
            self.install_path, self.verbose, {'last_version': self.config.tag_last_version}
        )
        # to use the DLL at link-time, Windows requires the lib file, so just build this on Mac/Linux
        if system() == 'Linux' or system() == 'Darwin':  # windows needs lib or def
            TestCAPIAccess().run(
                self.install_path, self.verbose, {}
            )
        else:
            if self.verbose:
                print("Building against the DLL at link time on Linux/Mac ONLY until we get a .lib file")
        # however, linking at run-time works just fine on all three platforms
        TestCppAPIDelayedAccess().run(
            self.install_path, self.verbose, {}
        )
        # Python may have trouble on Mac for right now, but should be able to work on Windows and Linux
        if system() == 'Linux' or system() == 'Windows':
            TestPythonAPIAccess().run(
                self.install_path, self.verbose, {}
            )
        else:
            if self.verbose:
                print("Running Python API Linux and Windows ONLY until we get the @executable_path resolved on Mac")
        # Documentation builds will be on all the platforms once I get pdftk and pdftotext or equivalent installed
        if system() == 'Linux':
            TestVersionInfoInDocumentation().run(
                self.install_path, self.verbose,
                {'pdf_file': 'AuxiliaryPrograms.pdf', 'version_string': self.config.this_version}
            )
        else:
            if self.verbose:
                print("Doing documentation tests on Linux ONLY until we get pdftk and pdftotext or equiv installed")
        os.chdir(saved_path)
