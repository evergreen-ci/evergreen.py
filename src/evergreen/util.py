"""Useful utilities for interacting with Evergreen."""
from datetime import datetime

EVG_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
EVG_DATE_FORMAT = '%Y-%m-%d'
EVG_DATE_INPUT_FORMAT = '"%Y-%m-%dT%H:%M:%S.000Z"'


def parse_evergreen_datetime(evg_date):
    """
    Convert an evergreen datetime string into a datetime object.

    :param evg_date: String to convert to a datetime.
    :return datetime version of date.
    """
    if not evg_date:
        return None
    return datetime.strptime(evg_date, EVG_DATETIME_FORMAT)


def format_evergreen_datetime(when):
    """
    Convert a datetime object into an evergreen consumable string.

    :param when: datetime to convert.
    :return: string evergreen can understand.
    """
    return when.strftime(EVG_DATE_INPUT_FORMAT)


def evergreen_input_to_output(input_date):
    """
    Convert a date from evergreen to a date to send back to evergreen.

    :param input_date: date to convert.
    :return: date to send to evergreen.
    """
    return format_evergreen_datetime(parse_evergreen_datetime(input_date))


def parse_evergreen_date(evg_date):
    """
    Convert an evergreen date string into a date object.

    :param evg_date: String to convert to a date.
    :return: date version of date.
    """
    if not evg_date:
        return None
    return datetime.strptime(evg_date, EVG_DATE_FORMAT).date()
