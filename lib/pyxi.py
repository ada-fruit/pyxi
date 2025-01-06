#!/usr/bin/env python3

import cliutil
from datetime import date
from product import CL_PRODUCTS
import re
import urllib

def get_site_info(path=cliutil.get_path()):

	matched = False

	if not matched:
		match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>dev\d+)/web/(?P<devsite>[^/]+)/)(?P<path>.*)', path)
		if match_data:
			matched = True
			match_data = match_data.groupdict()
			match_data['site_name'] = match_data['devsite'] + '.' + match_data['server']
			match_data['env_type'] = 'dev'

	if not matched:
		match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>[\w-]+)/(?P<client>[\w-]+)-test/test/)(?P<path>.*)', path)
		if match_data:
			matched = True
			match_data = match_data.groupdict()
			match_data['site_name'] = match_data['client'] + '-test'
			match_data['env_type'] = 'test'

	if not matched:
		match_data = re.match(r'^(?P<site_root>/mnt/(?P<server>[\w-]+)/(?P<client>[\w-]+)/(?P<prod_env>next|curr|prior)/)(?P<path>.*)', path)
		if match_data:
			matched = True
			match_data = match_data.groupdict()
			match_data['site_name'] = match_data['client'] + '-' + match_data['prod_env']
			match_data['env_type'] = 'prod'

	if matched:
		return match_data
	else:
		return { env_type: 'unknown' }


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
		suffix = args.suffix and args.suffix.lstrip('-') or get_iso8601_datestamp(strip_hyphens=True)
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
