import os
from tempfile import mkdtemp


class TestConfiguration:

    def __init__(self):
        self.this_version = '9.3'
        self.tag_this_version = 'v9.3.0-RC2'
        self.last_version = '9.2'
        self.tag_last_version = 'v9.2.0'

        # If this is turned on, it expects to find an asset named target_file_name in the download_dir
        self.skip_download = True
        self.skipped_download_dir = '/tmp/'

        # But if we are on Travis, we override it to always download a new asset
        if os.environ.get('TRAVIS', None) is not None:
            self.skip_download = False

        if self.skip_download:
            self.download_dir = self.skipped_download_dir
        else:
            self.download_dir = mkdtemp()
