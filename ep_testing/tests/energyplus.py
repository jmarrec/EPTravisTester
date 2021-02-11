import os
import subprocess

from ep_testing.exceptions import EPTestingException
from ep_testing.tests.base import BaseTest


class TestPlainDDRunEPlusFile(BaseTest):

    def name(self):
        return 'Test running IDF and make sure it exits OK'

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        if 'test_file' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass test_file in kwargs' % self.__class__.__name__)
        test_file = kwargs['test_file']
        print('* Running test class "%s" on file "%s"... ' % (self.__class__.__name__, test_file), end='')
        eplus_binary = os.path.join(install_root, 'energyplus')
        idf_path = os.path.join(install_root, 'ExampleFiles', test_file)
        if 'binary_sym_link' in kwargs:
            eplus_binary_to_use = os.path.join(os.getcwd(), 'ep_symlink')
            if verbose:
                print(f' [SYM-LINKED at {eplus_binary_to_use}]', end='')
            else:
                print(' [SYM-LINKED]', end='')
            os.symlink(eplus_binary, eplus_binary_to_use)
        else:
            eplus_binary_to_use = eplus_binary

        result = subprocess.run([eplus_binary_to_use, '-D', idf_path],
                                capture_output=True, check=False)
        try:
            # Throw if failed
            result.check_returncode()
            if verbose:
                print("STDOUT: {}".format(result.stdout.decode('utf-8')))
                print("STDERR: {}".format(result.stderr.decode('utf-8')))
            print(' [DONE]!')
        except subprocess.CalledProcessError:
            # If it fails, I assume you'd be interested in the stdout&stderr
            # to be able to diagnose
            print("STDOUT: {}".format(result.stdout.decode('utf-8')))
            print("STDERR: {}".format(result.stderr.decode('utf-8')))
            raise EPTestingException('EnergyPlus failed!')
