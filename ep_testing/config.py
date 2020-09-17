import os
import shutil
from tempfile import mkdtemp


class OS:
    Windows = 1
    Linux = 2
    Mac = 3


CONFIGURATIONS = {
    'ubuntu1804': {'os': OS.Linux, 'bitness': 'x64', 'asset_pattern': 'Linux-Ubuntu18.04-x86_64.tar.gz'},
    'ubuntu2004': {'os': OS.Linux, 'bitness': 'x64', 'asset_pattern': 'Linux-Ubuntu20.04-x86_64.tar.gz'},
    # 'mac1013': {'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS10.13-x86_64.tar.gz'},
    'mac1015': {'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS10.15-x86_64.tar.gz'},
    'win32': {'os': OS.Windows, 'bitness': 'x32', 'asset_pattern': 'Windows-i386.zip'},
    'win64': {'os': OS.Windows, 'bitness': 'x64', 'asset_pattern': 'Windows-x86_64.zip'},
}


class TestConfiguration:

    def __init__(self, run_config_key):

        # invalid keys are protected in the command's finalize_options method
        self.os = CONFIGURATIONS[run_config_key]['os']
        self.asset_pattern = CONFIGURATIONS[run_config_key]['asset_pattern']
        self.bitness = CONFIGURATIONS[run_config_key]['bitness']

        self.this_version = '9.4'
        self.tag_this_version = 'TestActionPackageBuilding6'
        self.last_version = '9.3'
        self.tag_last_version = 'v9.3.0'

        # If this is turned on, it expects to find an asset already downloaded at the specified location
        self.skip_download = False
        self.skipped_download_file = '/tmp/ep.tar.gz'

        # But if we are on Travis, we override it to always download a new asset
        if os.environ.get('TRAVIS'):
            self.skip_download = False

        self.download_dir = mkdtemp()
        if self.skip_download:
            target_file_name = 'ep.tar.gz'
            if self.os == OS.Windows:
                target_file_name = 'ep.zip'
            file_path = os.path.join(self.download_dir, target_file_name)
            shutil.copy(self.skipped_download_file, file_path)
