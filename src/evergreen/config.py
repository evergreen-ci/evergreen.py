# -*- encoding: utf-8 -*-
"""Get configuration about connecting to evergreen."""
from __future__ import absolute_import

import os
import subprocess
from typing import Dict, Optional

import yaml


class EvgAuth:  
    def __init__(self, config_path: str, use_oauth: bool = True) -> None:
        self.config_path: str = config_path
        self.use_oauth: bool = use_oauth

    def set_auth_headers(self, headers: Dict[str, str | bytes]) -> None:
        """Set the authentication headers for Evergreen API requests.

        :param headers: Dictionary of headers to update with authentication information.
        :param use_oauth: Whether to use OAuth token for authentication. Defaults to True.
        """
        if self.use_oauth:
            headers["Authorization"] = f"Bearer {self.get_oauth_token()}"
            return
        if not self.api_username:
            conf = read_evergreen_from_file(self.config_path)
            self.api_username: str = conf["user"]
            self.api_key: str = conf["api_key"]
        headers["Api-User"] = self.api_username
        headers["Api-Key"] = self.api_key

    def get_auth_headers(self) -> Dict[str, str | bytes]:
        """Get the authentication headers for Evergreen API requests.

        :return: Dictionary of headers with authentication information.
        """
        headers: Dict[str, str | bytes] = {}
        if self.use_oauth:
            headers["Authorization"] = f"Bearer {self.get_oauth_token()}"
        else:
            if not self.user:
                conf = read_evergreen_from_file(self.config_path)
                self.user: str = conf["user"]
                self.api_key: str = conf["api_key"]
            headers["Api-User"] = self.user
            headers["Api-Key"] = self.api_key
        return headers


    def get_oauth_token(self) -> str:
        """Get the OAuth token for authentication with Evergreen.

        :return: OAuth token string.
        """
        process = subprocess.run(f"evergreen login --config ${self.config_path}", shell=True)
        if process.returncode != 0:
            raise RuntimeError("Failed to login to Evergreen using the provided config.")
        process = subprocess.run(
            f"evergreen client get-oauth-token --config {self.config_path}",
            shell=True,
            capture_output=True,
        )
        if process.returncode != 0:
            raise RuntimeError("Failed to get OAuth token from Evergreen client.")
        return process.stdout.decode("utf-8").strip()


DEFAULT_NETWORK_TIMEOUT_SEC = 5 * 60
DEFAULT_API_SERVER = "https://evergreen.mongodb.com"
OAUTH_API_SERVER = "https://evergreen.corp.mongodb.com"
CONFIG_FILE_LOCATIONS = [
    os.path.expanduser(os.path.join("~", "cli_bin", ".evergreen.yml")),
    os.path.expanduser(os.path.join("~", ".evergreen.yml")),
]


def get_evergreen_config() -> Optional[str]:
    """
    Search known location for the evergreen config file.

    :return: First found evergreen configuration path.
    """
    for filename in [filename for filename in CONFIG_FILE_LOCATIONS if os.path.isfile(filename)]:
        return filename
    return None


def get_auth_from_config_path(config_path: str, use_oauth: bool = True) -> EvgAuth:
    """
    Get the evergreen authentication from the specified config path.

    :param config_path: Evergreen configuration location.
    :return: Authentication information for evergreen.
    """
    return EvgAuth(config_path, use_oauth)


def read_evergreen_from_file(filename: str) -> Dict:
    """
    Read evergreen config from given filename.

    :param filename: Filename to read config.
    :return: Config read from file.
    """
    with open(filename, "r") as fstream:
        return yaml.safe_load(fstream)


def read_evergreen_config() -> Optional[Dict]:
    """
    Search known location for the evergreen config file.

    :return: First found evergreen configuration.
    """
    for filename in [filename for filename in CONFIG_FILE_LOCATIONS if os.path.isfile(filename)]:
        return read_evergreen_from_file(filename)
    return None


def get_auth(use_oauth: bool = True) -> Optional[EvgAuth]:
    """
    Get the evergreen authentication object from the default locations. Convenience function.

    :return: Authentication information for evergreen.
    """
    conf_path = get_evergreen_config()
    if conf_path:
        return get_auth_from_config_path(conf_path, use_oauth)
    return None

