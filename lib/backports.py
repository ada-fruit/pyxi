from datetime import datetime
import re

RE_ISO_8601 = r'(\d{4})-?(\d{2})(?:-?(\d{2})(?:T(\d{2})(?::?(\d{2}))?(?::?(\d{2})(?:\.\d{3})?)?)?)?'


def datetime_fromisoformat(iso_date):
    # print('datetime_fromisoformat passed ' + iso_date)
    match = re.match(RE_ISO_8601, iso_date)
    datetime_args = [int(x) for x in list(filter(lambda x: x, match.groups()))]
    return datetime(*datetime_args)