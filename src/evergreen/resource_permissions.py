# -*- encoding: utf-8 -*-
"""Resource permissions representation of evergreen."""
from __future__ import absolute_import

from typing import TYPE_CHECKING, Any, Dict, List

from evergreen.base import _BaseEvergreenObject, evg_attrib

if TYPE_CHECKING:
    from evergreen.api import EvergreenApi


class UserResourcePermissions(_BaseEvergreenObject):
    """Representation of a single user's resource permissions."""

    user = evg_attrib("user")
    permissions = evg_attrib("permissions")

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """
        Create a UserResourcePermissions instance.

        :param json: json representing project.
        :param api: evergreen api object.
        """
        super().__init__(json, api)


class AllUserResourcePermissions(_BaseEvergreenObject):
    """Representation of all permissions held by users to a resource."""

    def __init__(self, json: Dict[str, Any], api: "EvergreenApi") -> None:
        """
        Create an AllUserResourcePemrissions instance.

        :param json: json representing project.
        :param api: evergreen api object.
        """
        super().__init__(json, api)

    @property
    def permissions(self) -> List[UserResourcePermissions]:
        """Fetch a list of user resource permissions."""
        return [
            UserResourcePermissions({"user": user, "permissions": permissions}, self._api)
            for user, permissions in self.json.items()
        ]
