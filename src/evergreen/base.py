# -*- encoding: utf-8 -*-
"""Task representation of evergreen."""
from __future__ import absolute_import

from evergreen.util import parse_evergreen_datetime, parse_evergreen_date


def evg_attrib(attrib_name, type_fn=None):
    """
    Create an attribute for the given evergreen property.

    This creates an attribute for the class that looks up the value via json. It is used to
    allow editors to show what attributes are available for a given evergreen object.

    :param attrib_name: name of attribute.
    :param type_fn: method to use to convert attribute by type.
    """

    def attrib_getter(instance):
        if type_fn:
            return type_fn(instance.json[attrib_name])
        return instance.json[attrib_name]

    return property(attrib_getter, doc='value of {}'.format(attrib_name))


def evg_datetime_attrib(attrib_name):
    """
    Create a datetime attribute for the given evergreen property.

    :param attrib_name: Name of attribute.
    """
    return evg_attrib(attrib_name, parse_evergreen_datetime)


def evg_date_attrib(attrib_name):
    """
    Create a date attribute for the given evergreen property.

    :param attrib_name: Name of attribute.
    """
    return evg_attrib(attrib_name, parse_evergreen_date)


class _BaseEvergreenObject(object):
    """Common evergreen object."""

    def __init__(self, json, api):
        """
        Create an instance of an evergreen task.
        """
        self.json = json
        self._api = api
        self._date_fields = None

    def _is_field_a_date(self, item):
        return self._date_fields and item in self._date_fields and self.json[item]

    def __getattr__(self, item):
        """Lookup an attribute if it exists."""
        if item in self.json:
            if self._is_field_a_date(item):
                return parse_evergreen_datetime(self.json[item])
            return self.json[item]
        raise TypeError('Unknown attribute {0}'.format(item))
