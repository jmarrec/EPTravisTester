import os
import subprocess
import urllib.request

from ep_testing.exceptions import EPTestingException
from ep_testing.tests.base import BaseTest


class TransitionOldFile(BaseTest):

    def name(self):
        return 'Test running 1ZoneUncontrolled.idf and make sure it exits OK'

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        if 'last_version' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass last_version in kwargs' % self.__class__.__name__)

        allow_failure = kwargs.get('allow_failure', False)

        last_version = kwargs['last_version']
        test_file = kwargs.get('test_file', '1ZoneUncontrolled.idf')
        print('* Running test class "%s" on file "%s"... ' % (self.__class__.__name__, test_file), end='')
        transition_dir = os.path.join(install_root, 'PreProcess', 'IDFVersionUpdater')
        all_transition_binaries = [
            f.path for f in os.scandir(transition_dir) if f.is_file() and f.name.startswith('Transition-')
        ]
        if len(all_transition_binaries) < 1:
            raise EPTestingException('Could not find any transition binaries...weird')
        all_transition_binaries.sort()
        most_recent_binary = all_transition_binaries[-1]
        idf_url = 'https://raw.githubusercontent.com/NREL/EnergyPlus/%s/testfiles/%s' % (last_version, test_file)
        saved_dir = os.getcwd()
        os.chdir(transition_dir)
        idf_path = os.path.join(transition_dir, test_file)
        try:
            _, headers = urllib.request.urlretrieve(idf_url, idf_path)
        except Exception as e:
            raise EPTestingException('Could not download file from prior release at %s; error: %s' % (idf_url, str(e)))

        result = subprocess.run([most_recent_binary, os.path.basename(idf_path)],
                                # capture_output added in python 3.7 only...
                                # capture_output=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False)
        try:
            # Throw if failed
            result.check_returncode()
            if verbose:
                print("STDOUT: {}".format(result.stdout.decode('utf-8')))
                print("STDERR: {}".format(result.stderr.decode('utf-8')))
            print(' [TRANSITIONED]! ', end='')
        except subprocess.CalledProcessError:
            # If it fails, I assume you'd be interested in the stdout&stderr
            # to be able to diagnose
            print("STDOUT: {}".format(result.stdout.decode('utf-8')))
            print("STDERR: {}".format(result.stderr.decode('utf-8')))
            msg = 'Transition failed!'
            if not allow_failure:
                raise EPTestingException(msg)
            else:
                print(msg)

        os.chdir(install_root)
        eplus_binary = os.path.join(install_root, 'energyplus')
        result = subprocess.run([eplus_binary, '-D', idf_path],
                                # capture_output added in python 3.7 only...
                                # capture_output=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False)
        try:
            # Throw if failed
            result.check_returncode()
            if verbose:
                print("STDOUT: {}".format(result.stdout.decode('utf-8')))
                print("STDERR: {}".format(result.stderr.decode('utf-8')))
            print(' [TRANSITIONED]! ', end='')
        except subprocess.CalledProcessError:
            # If it fails, I assume you'd be interested in the stdout&stderr
            # to be able to diagnose
            print("STDOUT: {}".format(result.stdout.decode('utf-8')))
            print("STDERR: {}".format(result.stderr.decode('utf-8')))
            msg = 'EnergyPlus failed to run Transitionned file!'
            if not allow_failure:
                raise EPTestingException(msg)
            else:
                print(msg)

        os.chdir(saved_dir)


# if __name__ == '__main__':
#     t = TransitionOldFile().run(
#         '/tmp/ep_package/EnergyPlus-9.3.0-5eeaa0ed25-Linux-x86_64', {'last_version': 'v9.2.0'}
#     )
