import os
from subprocess import check_call, STDOUT, CalledProcessError

from ep_testing.exceptions import EPTestingException


class BaseTest:

    def name(self):
        raise NotImplementedError('name() must be overridden by derived classes')

    def run(self, install_root: str, kwargs: dict):
        raise NotImplementedError('run() must be overridden by derived classes')


class TestPlainDDRunEPlusFile(BaseTest):

    def name(self):
        return 'Test running 1ZoneUncontrolled.idf and make sure it exits OK'

    def run(self, install_root: str, kwargs: dict):
        if 'testfile' not in kwargs:
            raise EPTestingException('Bad call to TestPlainRunEPlusFile -- must pass testfile in kwargs')
        test_file = kwargs['testfile']
        print('* Running test class "%s" on file "%s"... ' % (self.__class__.__name__ , test_file), end='')
        eplus_binary = os.path.join(install_root, 'energyplus')
        idf_path = os.path.join(install_root, 'ExampleFiles', test_file)
        dev_null = open(os.devnull, 'w')
        try:
            check_call([eplus_binary, '-D', idf_path], stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('EnergyPlus failed!')


class Tester:

    def __init__(self, install_path: str):
        self.install_path = install_path

    def run(self):
        saved_path = os.getcwd()
        os.chdir(self.install_path)
        try:
            TestPlainDDRunEPlusFile().run(self.install_path, {'testfile': '1ZoneUncontrolled.idf'})
            TestPlainDDRunEPlusFile().run(self.install_path, {'testfile': 'PythonPluginCustomOutputVariable.idf'})
        except Exception:
            raise
        finally:
            os.chdir(saved_path)
