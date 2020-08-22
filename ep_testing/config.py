import os
import platform
import shutil
from tempfile import mkdtemp


class TestConfiguration:

    def __init__(self):
        self.this_version = '9.4'
        self.tag_this_version = 'v9.4.0-IOFreeze-RC1'
        self.last_version = '9.3'
        self.tag_last_version = 'v9.3.0'

        # If this is turned on, it expects to find an asset named target_file_name in the download_dir
        self.skip_download = True
        self.skipped_download_file = '/tmp/ep.tar.gz'

        # But if we are on Travis, we override it to always download a new asset
        if os.environ.get('TRAVIS'):
            self.skip_download = False

        self.download_dir = mkdtemp()
        if self.skip_download:
            this_platform = platform.system()
            target_file_name = 'ep.tar.gz'
            if this_platform == 'Windows':
                target_file_name = 'ep.zip'
            file_path = os.path.join(self.download_dir, target_file_name)
            shutil.copy(self.skipped_download_file, file_path)
