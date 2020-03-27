from distutils import log
from typing import List
import os
import platform
import requests
import shutil
from subprocess import check_call, CalledProcessError
import urllib.request

from ep_testing.exceptions import EPTestingException
from ep_testing.config import TestConfiguration


class Downloader:
    Release_url = 'https://api.github.com/repos/NREL/EnergyPlus/releases'
    User_url = 'https://api.github.com/user'

    def __init__(self, config: TestConfiguration, download_dir: str, announce: callable = None):
        self.release_tag = config.TAG_THIS_VERSION
        self.download_dir = download_dir
        self.announce = announce  # hijacking this instance method is mildly dangerous, like 1/5 danger stars
        github_token = os.environ.get('GITHUB_TOKEN', None)
        if github_token is None:
            raise EPTestingException('GITHUB_TOKEN not found in environment, cannot continue')
        self.auth_header = {'Authorization': 'token %s' % github_token}
        user_response = requests.get(self.User_url, headers=self.auth_header)
        if user_response.status_code != 200:
            raise EPTestingException('Invalid call to Github API -- check GITHUB_TOKEN validity')
        self._my_print('Executing download operations as Github user: ' + user_response.json()['login'])
        this_platform = platform.system()
        extract_dir_name = 'ep_package'
        self.extract_path = os.path.join(download_dir, extract_dir_name)
        if this_platform == 'Linux':
            self.asset_pattern = 'Linux-x86_64.tar.gz'
            target_file_name = 'ep.tar.gz'
            # tar -xzf ep.tar.gz -C ep_package
            self.extract_command = ['tar', '-xzf', target_file_name, '-C', self.extract_path]
        elif this_platform == 'Darwin':
            self.asset_pattern = 'Darwin-x86_64.tar.gz'
            target_file_name = 'ep.tar.gz'
            # tar -xzf ep.tar.gz -C ep_package
            self.extract_command = ['tar', '-xzf', target_file_name, '-C', self.extract_path]
        elif this_platform == 'Windows':
            self.asset_pattern = 'Windows-x86_64.zip'
            target_file_name = 'ep.zip'
            # 7z x ep.zip -oep_package
            self.extract_command = ['7z.exe', 'x', target_file_name, '-o' + self.extract_path]
        else:
            raise EPTestingException('Unknown platform -- ' + this_platform)
        releases = self._get_all_packages()
        matching_release = self._find_matching_release(releases)
        asset = self._find_matching_asset_for_release(matching_release)
        self.download_path = os.path.join(download_dir, target_file_name)
        if config.SKIP_DOWNLOAD:
            if not os.path.exists(self.download_path):
                raise EPTestingException('Download skipped, but package not available at ' + self.download_path)
        else:
            self._download_asset(asset)
        self._extracted_install_path = self._extract_asset()

    def _get_all_packages(self) -> List[dict]:
        """Get all releases from this url"""
        try:
            releases = []
            next_page_url = self.Release_url
            while next_page_url:
                response = requests.get(next_page_url, headers=self.auth_header)
                these_releases = response.json()
                self._my_print('Got release response, number on this query = %i' % len(these_releases), log.DEBUG)
                releases.extend(these_releases)
                raw_next_page_url = response.headers.get('link', None)
                if raw_next_page_url is None:
                    break
                if 'rel="next"' not in raw_next_page_url:
                    break
                next_page_url = self._sanitize_next_page_url(raw_next_page_url)
            self._my_print('Got total release list: Total number of releases = %i' % len(releases), log.DEBUG)
        except Exception as e:
            raise EPTestingException('Could not download list of releases' + str(e))
        return releases

    def _find_matching_release(self, releases: List[dict]) -> dict:
        full_list_of_release_names = []
        for release in releases:
            full_list_of_release_names.append(release['tag_name'])
            if release['tag_name'] == self.release_tag:
                self._my_print('Found release with tag_name = ' + self.release_tag)
                return release
        raise EPTestingException('Did not find matching tag, searching for %s, full list = [%s\n]' % (
            self.release_tag,
            ['\n%s' % x for x in full_list_of_release_names]
        ))

    @staticmethod
    def _sanitize_next_page_url(next_page_url: str) -> str:
        if next_page_url[0] != '<':
            # only sanitize the next pagers with the braces
            return next_page_url
        braced_url = next_page_url.split(';')[0]
        remove_first_brace = braced_url[1:]
        remove_last_brace = remove_first_brace[:-1]
        return remove_last_brace

    def _find_matching_asset_for_release(self, release: dict) -> dict:
        asset_url = release['assets_url']
        # making an assumption that I don't need to paginate these -- we won't have > 30 assets per release
        assets = requests.get(asset_url, headers=self.auth_header).json()
        full_list_of_asset_names = []
        for asset in assets:
            full_list_of_asset_names.append(asset['name'])
            if self.asset_pattern in asset['name']:
                self._my_print('Found asset with name "%s": "%s"' % (self.asset_pattern, asset['name']))
                return asset

    def _download_asset(self, asset: dict) -> None:
        try:
            _, headers = urllib.request.urlretrieve(asset['browser_download_url'], self.download_path)
            self._my_print('Asset downloaded to ' + self.download_path)
        except Exception as e:
            raise EPTestingException(
                'Could not download asset from %s; error: %s' % (asset['browser_download_url'], str(e))
            )

    def _extract_asset(self) -> str:
        """Attempts to extract the downloaded package, returns the path to the E+ install subdirectory"""
        saved_working_directory = os.getcwd()
        os.chdir(self.download_dir)
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        try:
            os.makedirs(self.extract_path)
        except Exception as e:
            raise EPTestingException('Could not create extraction path at %s; error: %s' % (self.extract_path, str(e)))
        try:
            check_call(self.extract_command)
        except CalledProcessError as e:
            raise EPTestingException("Extraction failed with this error: " + str(e))
        # should result in a single new directory inside the extract path, like: /extract/path/EnergyPlus-V1-abc-Linux
        all_sub_folders = [f.path for f in os.scandir(self.extract_path) if f.is_dir()]
        if len(all_sub_folders) > 1:
            raise EPTestingException('Extracted EnergyPlus package has more than one directory, problem.')
        os.chdir(saved_working_directory)
        return all_sub_folders[0]

    def _my_print(self, message: str, level: object = log.INFO) -> None:
        if self.announce:
            self.announce(message, level)
        else:
            print(message)

    def extracted_install_path(self) -> str:
        return self._extracted_install_path
