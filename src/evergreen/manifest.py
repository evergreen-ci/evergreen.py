from __future__ import absolute_import

from evergreen.base import _BaseEvergreenObject


class ManifestModule(_BaseEvergreenObject):
    """
    Represents a module in the evergreen manifest.
    """

    def __init__(self, name, json, api):
        """
        Create an instance of an evergreen manifest module.

        :param json: json representing manifest.
        :param api: evergreen api object
        """
        super(ManifestModule, self).__init__(json, api)
        self.name = name


class Manifest(_BaseEvergreenObject):
    """
    Representation of an evergreen manifest.
    """

    def __init__(self, json, api):
        """
        Create an instance of an evergreen version manifest.

        :param json: json representing manifest.
        :param api: evergreen api object.
        """
        super(Manifest, self).__init__(json, api)

    @property
    def modules(self):
        """Map of modules in this manifest."""
        if 'modules' not in self.json:
            return None

        modules = self.json['modules'].items()

        return {
            module_key: ManifestModule(module_key, module_value, self._api)
            for module_key, module_value in modules
        }
