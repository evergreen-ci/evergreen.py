# -*- encoding: utf-8 -*-
"""Get configuration about connecting to evergreen."""
from __future__ import absolute_import

import os
from collections import namedtuple
from typing import Dict, Optional

import yaml

EvgAuth = namedtuple("EvgAuth", ["username", "api_key"])
OidcConfig = namedtuple("OidcConfig", ["issuer", "client_id", "connector_id", "token_file_path"])

DEFAULT_NETWORK_TIMEOUT_SEC = 5 * 60
DEFAULT_API_SERVER = "https://evergreen.mongodb.com"
DEFAULT_API_SERVER_OIDC = "https://evergreen.corp.mongodb.com"
CONFIG_FILE_LOCATIONS = [
    os.path.expanduser(os.path.join("~", "cli_bin", ".evergreen.yml")),
    os.path.expanduser(os.path.join("~", ".evergreen.yml")),
]


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


def get_oauth_config_from_dict(oauth_dict: Dict) -> OidcConfig:
    """
    Get OIDC configuration from a dictionary.

    :param oauth_dict: Dictionary containing oauth configuration.
    :return: OidcConfig object.
    """
    return OidcConfig(
        issuer=oauth_dict["issuer"],
        client_id=oauth_dict["client_id"],
        connector_id=oauth_dict["connector_id"],
        token_file_path=oauth_dict.get("token_file_path"),
    )


def get_oauth_config_from_config(config: Dict) -> Optional[OidcConfig]:
    """
    Get OIDC configuration from the config dictionary, if it exists.

    :param config: Evergreen configuration.
    :return: OidcConfig if present, None otherwise.
    """
    if "oauth" in config:
        return get_oauth_config_from_dict(config["oauth"])
    return None


def get_auth_from_config(config: Dict) -> Optional[EvgAuth]:
    """
    Get the evergreen authentication from the specified config dict.

    :param config: Evergreen configuration.
    :return: Authentication information for evergreen, or None if no API key auth is configured.
    """
    if "user" in config and "api_key" in config:
        return EvgAuth(config["user"], config["api_key"])
    return None


def get_auth() -> Optional[EvgAuth]:
    """
    Get the evergreen authentication object from the default locations. Convenience function.

    :return: Authentication information for evergreen.
    """
    conf = read_evergreen_config()
    if conf:
        return get_auth_from_config(conf)
    return None
