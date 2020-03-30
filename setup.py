import distutils.cmd
import distutils.log
from setuptools import setup
from ep_testing.downloader import Downloader
from ep_testing.tester import Tester
from ep_testing.config import TestConfiguration


class Runner(distutils.cmd.Command):
    """A custom command to run E+ tests using `setup.py run`"""

    description = 'Run E+ tests on installers for this platform'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        verbose = True
        c = TestConfiguration()
        self.announce('Attempting to test tag name: %s' % c.tag_this_version, level=distutils.log.INFO)
        d = Downloader(c, self.announce)
        self.announce('EnergyPlus package extracted to: ' + d.extracted_install_path(), level=distutils.log.INFO)
        t = Tester(c, d.extracted_install_path(), verbose)
        # unhandled exceptions should cause this to fail
        t.run()


setup(
    name='EPTravisTester',
    version='0.1',
    packages=['ep_testing'],
    url='github.com/nrel/energyplus',
    license='',
    author='edwin',
    author_email='',
    description='A small set of test scripts that will pull E+ installers and run a series of tests on them',
    cmdclass={
        'run': Runner,
    },
)
