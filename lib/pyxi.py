#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import cliutil
from datetime import date
from product import CL_PRODUCTS
import re
import urllib


# Factory pattern for creating dev sites.
# Instead of classes with static members, these could all be instances
# of the same class, but I think it might be useful to extend these
# with other environment-specific behavior in the future.
# Constructor will throw if parsing fails.
def create_environment(site_path):
    new_site = None
    for cls in CourseleafEnvironment.__subclasses__():
        try:
            new_site = cls(site_path)
        except Exception:
            pass

    if new_site is not None:
        return new_site

    raise 'Failed to parse any type of CourseLeaf environment ' \
        'from path: ' + site_path


class CourseleafEnvironment(metaclass=ABCMeta):
    # The environment type
    # e.g., "test", "dev", "prod"
    @property
    @staticmethod
    @abstractmethod
    def environment_type():
        pass

    # A regex with named capture groups to parse the siteroot path
    @property
    @staticmethod
    @abstractmethod
    def site_path_pattern():
        pass

    # The site name
    # e.g., "clientname-extension.dev8", "clientname-test", "clientname-next"
    @property
    @staticmethod
    @abstractmethod
    def site_name():
        pass

    def __init__(self, site_path):
        match_data = re.match(self.site_path_pattern, site_path)
        for capture_group, capture_body in match_data.items():
            self[capture_group] = capture_body


class DevEnvironment(CourseleafEnvironment):
    environment_type = 'dev'
    site_path_pattern = \
        r'^(?P<site_root>' \
        r'/mnt/(?P<server>dev\d+)' \
        r'/web/(?P<devsite>[^/]+)/)' \
        r')(?P<path>.*)'

    def __init__(self, site_path):
        super.__init__(site_path)
        self.site_name = f'{self.devsite}.{self.server}'


class TestEnvironment(CourseleafEnvironment):
    environment_type = 'test'
    site_path_pattern = \
        r'^(?P<site_root>' \
        r'/mnt/(?P<server>[\w-]+)/' \
        r'(?P<client>[\w-]+)-test/test/)' \
        r')(?P<path>.*)'

    def __init__(self, site_path):
        super().__init__(site_path)
        self.site_name = self.client + '-test'


class ProdEnvironment(CourseleafEnvironment):
    environment_type = 'prod'
    site_path_pattern = \
        r'^(?P<site_root>' \
        r'/mnt/(?P<server>[\w-]+)' \
        r'/(?P<client>[\w-]+)/' \
        r'(?P<prod_env>next|curr|prior)' \
        r')(?P<path>.*)'

    def __init__(self, site_path):
        super().__init__(site_path)
        self.site_name = f'{self.client}-{self.prod_env}'


# def get_site_info(path=cliutil.get_path()):
#     matched = False

#     if not matched:
#         match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>dev\d+)/web/(?P<devsite>[^/]+)/)(?P<path>.*)', path)
#         if match_data:
#             matched = True
#             match_data = match_data.groupdict()
#             match_data['site_name'] = match_data['devsite'] + '.' + match_data['server']
#             match_data['env_type'] = 'dev'

#     if not matched:
#         match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>[\w-]+)/(?P<client>[\w-]+)-test/test/)(?P<path>.*)', path)
#         if match_data:
#             matched = True
#             match_data = match_data.groupdict()
#             match_data['site_name'] = match_data['client'] + '-test'
#             match_data['env_type'] = 'test'

#     if not matched:
#         match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>[\w-]+)/(?P<client>[\w-]+)/(?P<prod_env>next|curr|prior)/)(?P<path>.*)', path)
#         if match_data:
#             matched = True
#             match_data = match_data.groupdict()
#             match_data['site_name'] = match_data['client'] + '-' + match_data['prod_env']
#             match_data['env_type'] = 'prod'

#     if matched:
#         return match_data
#     else:
#         return { env_type: 'unknown' }


def get_site_root(path=cliutil.get_path()):
    site_info = get_site_info(path)
    return site_info['site_root']


def show_versions(args) -> str:
    product_info_rows = []
    column_width = [0, 0]
    for key, product in CL_PRODUCTS.items():
        product_info = { 'name': product.name or key, 'version': [product.get_version()] }
        version_match = re.match(r'([^(]+) (\([^)]+\))', product_info['version'][0])
        column_width[0] = max(column_width[0], len(product_info['name']))
        if version_match:
            match_groups = version_match.groups()
            column_width[1] = max(column_width[1], len(match_groups[0]))
            product_info['version'] = match_groups
        product_info_rows.append(product_info)
    out_lines = []
    for row in product_info_rows:
        out = row['name'] + (' ' * (column_width[0] - len(row['name'])))
        out += ' : '
        out += row['version'][0]
        if len(row['version']) > 1:
            out += ' ' * (1 + column_width[1] - len(row['version'][0]))
            out += row['version'][1]
        out_lines.append(out)
    return '\n'.join(out_lines)


def print_link_to_cpclsite(args) -> str:
    url = f'https://{get_cpclsite_host()}/'

    if args.destination:
        url += 'localcopy.cgi'
        url += f'?src={urllib.parse.quote(args.source)}'
        url += f'&dst={urllib.parse.quote(args.destination)}'
    else:
        url += 'cpclsite-wrapper.cgi'
        url += f'?clientid={urllib.parse.quote(args.source)}'
        url += f'&src={urllib.parse.quote(args.prodenv)}'
        suffix = args.suffix.lstrip('-') if args.suffix \
            else get_iso8601_datestamp(strip_hyphens=True)
        if not args.anonymous:
            suffix = prepend_username(suffix)
        url += f'&extension={urllib.parse.quote(suffix)}'

    return url


def get_cpclsite_host() -> str:
    return 'cpclsite.' + cliutil.get_dev_hostname()


def get_iso8601_datestamp(strip_hyphens=False) -> str:
    stamp = str(date.today())
    if strip_hyphens:
        stamp = stamp.replace('-', '')
    return stamp


def prepend_username(text) -> str:
    uname = cliutil.get_username()
    if not re.match('\\b' + re.escape(uname) + '\\b', text):
        text = uname + '-' + text.lstrip('-')
    return text


def print_link_to_devsite(args) -> str:
    return str(args)


# TODO
def print_applied_patches(args) -> str:
    return 'print_applied_patches called with args=' + str(args)


# TODO
def print_patch_details(args) -> str:
    return 'print_patch_details called with args=' + str(args)


# TODO
def print_devsites_with_patch(args) -> str:
    return 'print_devsites_with_patch called with args=' + str(args)


# TODO parse clientname-test, clientname/next, dev-site-name, dev-site-name.dev7, etc
def parse_environment_nickname(nick) -> dict:
    pass


# TODO
def parse_patch_label(label) -> dict:
    pass
