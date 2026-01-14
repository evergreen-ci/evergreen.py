# -*- encoding: utf-8 -*-
"""OIDC token management for Evergreen API authentication."""
from __future__ import absolute_import

import json
import os
import time
from typing import TYPE_CHECKING, Optional

import jwt
import requests
import structlog

from evergreen.config import OidcConfig

if TYPE_CHECKING:
    from evergreen.api import EvergreenApi

LOGGER = structlog.getLogger(__name__)


class OidcToken:
    """Represents an OIDC access token."""

    def __init__(self, access_token: str, refresh_token: str):
        """
        Initialize an OIDC token.

        :param access_token: The access token JWT string.
        :param refresh_token: Refresh token for obtaining new access tokens.
        """
        self.access_token = access_token
        self.refresh_token = refresh_token

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if token is expired by decoding the JWT and checking the exp claim.

        :param buffer_seconds: Number of seconds to consider as buffer before actual expiration.
        :return: True if token is expired or about to expire, False otherwise.
        """
        claims = jwt.decode(self.access_token, options={"verify_signature": False})
        exp_timestamp = claims["exp"]
        current_time = time.time()
        return current_time >= (exp_timestamp - buffer_seconds)

    @classmethod
    def from_dict(cls, data: dict) -> "OidcToken":
        """
        Create OidcToken from dictionary (e.g., from JSON file).

        :param data: Dictionary containing 'access_token' and 'refresh_token'.
        :return: OidcToken instance.
        """
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
        )

    def to_dict(self) -> dict:
        """
        Convert token to dictionary (for JSON serialization).

        :return: Dictionary representation of the token.
        """
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }

    def get_username_from_claims(self) -> str:
        """
        Extract username from JWT token claims.

        Decodes the JWT (without verification) and extracts the username
        from common claim names (preferred_username, email, sub, name).

        :return: Username extracted from token claims.
        :raises KeyError: If no recognized username claim is found in token.
        """
        # Decode JWT without verification (we're just reading claims)
        claims = jwt.decode(self.access_token, options={"verify_signature": False})

        # Try common username claim names
        for claim_name in ["preferred_username", "email", "sub", "name"]:
            if claim_name in claims:
                username = claims[claim_name]
                # If it's an email, extract the part before @
                if "@" in username and claim_name == "email":
                    username = username.split("@")[0]
                return username

        raise KeyError("No recognized username claim found in token")


class OidcTokenManager:
    """Manages OIDC token acquisition and caching."""

    def __init__(self, oidc_config: OidcConfig, timeout: Optional[int] = None):
        """
        Initialize the OIDC token manager.

        :param oidc_config: OIDC configuration.
        :param timeout: Optional timeout for HTTP requests in seconds.
        """
        self.oidc_config = oidc_config
        self.timeout = timeout
        self._token: Optional[OidcToken] = None

    def get_token(self) -> str:
        """
        Get a valid access token, acquiring or refreshing if necessary.

        :return: Access token string.
        """
        # Try to load from cache file first
        if self._token is None and self.oidc_config.token_file_path:
            try:
                self._token = self._load_token_from_file()
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                raise RuntimeError(
                    "Evergreen token file is invalid or missing. Do you need to run `evergreen login`?"
                ) from e

        # If we have a valid token, return it
        if self._token and not self._token.is_expired():
            return self._token.access_token

        # Token is expired or missing. Try to refresh if we have a refresh token
        if self._token and self._token.refresh_token:
            LOGGER.debug("Attempting to refresh expired token using refresh token")
            try:
                self._token = self._refresh_token(self._token.refresh_token)
            except requests.HTTPError as e:
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    raise RuntimeError(
                        f"Refresh token is invalid or expired. Do you need to re-run `evergreen login` or remove {self.oidc_config.token_file_path}?"
                    ) from e
                raise
            # Cache the refreshed token if configured
            if self.oidc_config.token_file_path:
                self._save_token_to_file(self._token)
            return self._token.access_token

        raise RuntimeError(
            "No valid OIDC token available and no refresh token present. Do you need to run `evergreen login`?"
        )

    def _load_token_from_file(self) -> OidcToken:
        """
        Load token from the configured token file.

        :return: OidcToken loaded from file.
        :raises FileNotFoundError: If token file doesn't exist.
        :raises json.JSONDecodeError: If token file is corrupted.
        :raises KeyError: If token file is missing required fields.
        """
        with open(self.oidc_config.token_file_path, "rb") as f:
            data = json.load(f)
            return OidcToken.from_dict(data)

    def _save_token_to_file(self, token: OidcToken) -> None:
        """
        Save token to the configured token file.

        :param token: Token to save.
        """
        if not self.oidc_config.token_file_path:
            return

        # Ensure directory exists
        directory = os.path.dirname(self.oidc_config.token_file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(self.oidc_config.token_file_path, "w") as f:
            json.dump(token.to_dict(), f)

    def _refresh_token(self, refresh_token: str) -> OidcToken:
        """
        Refresh an access token using a refresh token.

        :param refresh_token: The refresh token to use.
        :return: OidcToken instance with new access token.
        :raises RuntimeError: If refresh fails.
        """
        metadata = self._get_provider_metadata()
        token_endpoint = metadata.get("token_endpoint")

        if not token_endpoint:
            raise RuntimeError("OIDC provider metadata missing token_endpoint")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.oidc_config.client_id,
        }

        response = requests.post(token_endpoint, data=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        return OidcToken(
            access_token=data["access_token"],
            refresh_token=data.get(
                "refresh_token", refresh_token
            ),  # Use new refresh token if provided, else keep old one
        )

    def _get_provider_metadata(self) -> dict:
        """
        Fetch OIDC provider metadata from the well-known configuration endpoint.

        :return: Provider metadata dictionary.
        :raises RuntimeError: If metadata fetch fails.
        """
        metadata_url = f"{self.oidc_config.issuer}/.well-known/openid-configuration"
        response = requests.get(metadata_url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()


def get_username_from_api(api: "EvergreenApi") -> str:
    """
    Extract username from an EvergreenApi instance.

    Works with both API key auth and OIDC auth by extracting the username
    from the appropriate source.

    :param api: The EvergreenApi instance.
    :return: Username extracted from either API key auth or OIDC token.
    :raises ValueError: If no username can be determined from auth configuration.
    """
    # Try API key auth first
    if api._auth:
        return api._auth.username

    # Try OIDC auth
    if api._oidc_token_manager:
        # Get the token (this will load from file if needed)
        api._oidc_token_manager.get_token()

        # Now access the token object that was stored
        token = api._oidc_token_manager._token
        if token and isinstance(token, OidcToken):
            return token.get_username_from_claims()

    raise ValueError("Could not determine username from API authentication configuration")
