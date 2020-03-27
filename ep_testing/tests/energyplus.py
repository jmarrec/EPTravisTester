import os
from subprocess import check_call, CalledProcessError, STDOUT

from ep_testing.exceptions import EPTestingException
from ep_testing.tests.base import BaseTest


class TestPlainDDRunEPlusFile(BaseTest):

    def name(self):
        return 'Test running IDF and make sure it exits OK'

    def run(self, install_root: str, kwargs: dict):
        if 'test_file' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass test_file in kwargs' % self.__class__.__name__)
        test_file = kwargs['test_file']
        print('* Running test class "%s" on file "%s"... ' % (self.__class__.__name__, test_file), end='')
        eplus_binary = os.path.join(install_root, 'energyplus')
        idf_path = os.path.join(install_root, 'ExampleFiles', test_file)
        dev_null = open(os.devnull, 'w')
        try:
            check_call([eplus_binary, '-D', idf_path])  # , stdout=dev_null, stderr=STDOUT)
            print(' [DONE]!')
        except CalledProcessError:
            raise EPTestingException('EnergyPlus failed!')
