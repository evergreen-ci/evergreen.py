# -*- encoding: utf-8 -*-
"""Get configuration about connecting to evergreen."""
from __future__ import absolute_import

import os
import subprocess
from collections import namedtuple
from typing import Dict, Optional

import yaml

EvgAuth = namedtuple("EvgAuth", ["username", "api_key", "jwt"])

DEFAULT_NETWORK_TIMEOUT_SEC = 5 * 60
DEFAULT_API_SERVER = "https://evergreen.mongodb.com"  # for use with api key
DEFAULT_CORP_API_SERVER = "https://evergreen.corp.mongodb.com"  # for use with JWT

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


def get_auth_from_config(config: Dict) -> EvgAuth:
    """
    Get the evergreen authentication from the specified config dict.

    :param config: Evergreen configuration.
    :return: Authentication information for evergreen.
    """
    return EvgAuth(username=config.get("user", ""), api_key=config.get("api_key", ""), jwt="")


def get_auth() -> Optional[EvgAuth]:
    """
    Get the evergreen authentication object. Falls back to JWT if no api_key is found in config.

    :return: Authentication information for evergreen.
    """
    conf = read_evergreen_config()

    if conf:
        auth = get_auth_from_config(conf)
        if auth.api_key:  # Only return auth if it has an api_key
            return auth

    # Try to get JWT if no api_key found
    if jwt := get_jwt():
        return EvgAuth(username="", api_key="", jwt=jwt)
    return None


def get_jwt() -> Optional[str]:
    """
    Get a JWT token using the 'kanopy-oidc' command.

    :return: JWT token if successful, None otherwise.
    """
    try:
        process = subprocess.Popen(
            ["kanopy-oidc", "login", "-n", "-f", "device"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        jwt = get_jwt_from_process(process)
        process.wait()

        if process.returncode != 0:
            print(
                f"Warning: evergreen client jwt command failed with return code {process.returncode}"
            )
            return None
        elif not jwt:
            print("Warning: No JWT token was obtained from evergreen client")
            return None

        return jwt

    except FileNotFoundError:
        print("Warning: evergreen client not found in PATH")
    except Exception as e:
        print(f"Warning: Error getting JWT token: {str(e)}")

    return None


def get_jwt_from_process(process: subprocess.Popen) -> Optional[str]:
    """
    Extract JWT token from process output while displaying other output to user.

    :param process: Subprocess with stdout and stderr pipes
    :return: JWT token if found, None otherwise
    """
    jwt = None

    if process.stdout:
        for line in process.stdout:
            # Check if line looks like a JWT (starts with 'ey' and is long)
            if len(line) > 30 and line.startswith("ey"):
                jwt = line.strip()
            else:
                print(line.strip())  # Show non-JWT output to user

    # Show any error output
    if process.stderr:
        for line in process.stderr:
            print(line.strip())

    return jwt
