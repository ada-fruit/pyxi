# TODO: on cl10, all CGI versions on the site should match

from abc import ABC, abstractmethod
import cliutil
import os
# from pathlib import Path
import re
from subprocess import CalledProcessError
from termcolor import colored


class Crawler(ABC):
    def execute_at_path(self, cmd, cwd=cliutil.get_path(), exe=None):
        return cliutil.get_shell_output(cmd, cwd=cwd, executable=exe)

    def read_at_path(self, path, filename):
        file_contents = ''
        file_path = os.path.join(cliutil.get_path(), path, filename)
        with open(file_path, 'r') as f:
            file_contents = '\n'.join(f.readlines())
        return file_contents


class Product(Crawler):
    def __init__(self, name, location):
        self.name = name
        self.location = location

    def get_version(self):
        try:
            return self.find_version()
        except Exception:
            return 'not found'

    @abstractmethod
    def find_version(self):
        pass


class CgiProduct(Product):
    def __init__(self, name, location, cgi_filename, version_arguments):
        super().__init__(name, location)
        self.cgi_filename = cgi_filename
        self.version_arguments = version_arguments
        self.rel_path = os.path.join(location, self.cgi_filename)
        self.cgi_path = os.path.join(cliutil.get_path(), self.rel_path)
        self.cli_args = ' '.join(self.version_arguments)

    def find_version(self):

        shell_cmd = f'{self.cgi_path} {self.cli_args}'

        try:
            self.check_permissions()
            shell_out = cliutil.get_shell_output(shell_cmd).strip()

        except CalledProcessError as e:
            return self.handle_error_cpe(e)

        except PermissionError:
            return 'not found (you do not have execute permissions)'

        except Exception as e:
            print(colored(
                'warn: other problem: ' + self.rel_path + ': ' + str(e),
                'yellow'
                ))
            return 'not found'

        # except Exception:
        #     print(colored(
        #         'error: failed to detect cgi version: ' + self.rel_path,
        #         'red'
        #          ))
        #     return 'not found'

        else:
            return shell_out

        return 'not found (f)'

    def handle_error_cpe(self, e):
        stderr = '' if e.stderr is None else e.stderr.decode('utf-8')

        is_wrong_rhel = (
            f'{self.cgi_path}: error while loading shared libraries' in stderr
            )
        if is_wrong_rhel:
            print(colored(
                'error: possibly, wrong RHEL version: ' + self.rel_path,
                'red'
                ))
            return 'not found (looks like wrong RHEL version)'

        is_missing_file = (
            f'{self.cgi_path}: No such file or directory' in stderr
            )
        if is_missing_file:
            # print(colored(
            # 'warn: possibly, file does not exist: ' + self.rel_path,
            # 'yellow'
            # ))
            return 'not found (file does not exist)'

        print(colored(
            f'fail: failed to detect cgi version: {self.rel_path}',
            'red'
            ))

        return 'not found'

    # quick and dirty, sorry
    def check_permissions(self):
        perms_cmd = f'stat {self.cgi_path} -c %#A'

        try:
            perms = cliutil.get_shell_output(perms_cmd).strip()
        except Exception:
            return

        if len(perms) != 10:
            raise Exception('Cannot parse permissions: ' + perms)

        user_exec = perms[3] == 'x'
        group_exec = perms[6] == 'x'

        if not user_exec:
            # print(colored(
            # f'error: no execute permissions: {self.rel_path} ({perms})',
            # 'red'
            # ))
            raise PermissionError('cannot execute version command')

        elif not group_exec:
            # print(colored(
            # f'warn: possibly, bad permissions: {self.rel_path} ({perms})',
            # 'yellow'
            # ))
            pass

        return True


class CourseleafCgiProduct(CgiProduct):

    def find_version(self):
        version = super().find_version()

        print_out = re.sub(
            r'\bversion ([\d.]+) (\d\d) (\d\d) (\d{4}) \d\d:\d\d:\d\d',
            r'\1 (\4-\2-\3)',
            version)
        return print_out


class GitProduct(Product):
    def find_version(self):
        version = self.execute_at_path(
            'show-current-branch', self.location).strip()
        if version == 'No git repository here, not on a branch':
            version = 'not a git repo'
        return version


class GitProductWithVersionFile(GitProduct):
    def __init__(self, name, location, version_filename):
        super().__init__(name, location)
        self.version_filename = version_filename or 'clver.txt'

    def find_version(self):
        git_version = super().find_version()
        file_version = 'no ' + self.version_filename
        try:
            file_version = self.read_at_path(
                self.location, self.version_filename)
            file_version = file_version.strip()
        except Exception:
            pass

        if file_version == 'not found':
            file_version = None
        if git_version == 'not found':
            git_version = None

        if file_version and git_version:
            return f'{file_version} ({git_version})'
        elif git_version:
            return f'no {self.version_filename} ({git_version})'
        elif file_version:
            return ''
        else:
            return 'not found'


class GitProductWithParsedVersion(GitProduct):
    def __init__(self, name, location, version_command):
        super().__init__(name, location)
        self.version_command = version_command

    def find_version(self):
        git_version = super().find_version()
        grep_version = 'not found'
        try:
            grep_version = self.execute_at_path(
                self.version_command, self.location)
            grep_version = grep_version.strip()
        except Exception:
            pass

        if git_version and git_version != 'not found':
            return f'{grep_version} ({git_version})'
        else:
            return grep_version


CL_PRODUCTS = {
    'core': CourseleafCgiProduct(
        'Core CGI',
        'web/courseleaf',
        'courseleaf.cgi',
        ['-v']),
    'ribbit': CourseleafCgiProduct(
        'Ribbit CGI',
        'web/ribbit',
        'index.cgi',
        ['-v']),
    'api': CourseleafCgiProduct(
        'API CGI',
        'web/api',
        'index.cgi',
        ['-v']),
    'admin-remote': CourseleafCgiProduct(
        'Remote CGI',
        'web/admin/remote',
        'index.cgi',
        ['-v']),
    'uas-core-cl': CourseleafCgiProduct(
        'UAS Core courseleaf.cgi',
        'web/courseleaf/patch',
        'courseleaf.cgi',
        ['-v']),
    'uas-core-clpatch': CourseleafCgiProduct(
        'UAS Core courseleaf.patch.cgi',
        'web/courseleaf/patch',
        'courseleaf.patch.cgi',
        ['-v']),
    'uas-core-assets-ribbit': CourseleafCgiProduct(
        'UAS Core assets/ribbit.cgi',
        'web/courseleaf/patch/assets',
        'ribbit.cgi',
        ['-v']),
    'cat': GitProductWithVersionFile(
        'CAT',
        'web/courseleaf',
        'clver.txt'),
    'cim': GitProductWithVersionFile(
        'CIM',
        'web/courseleaf/cim',
        'clver.txt'),
    'clss': GitProductWithParsedVersion(
        'CLSS',
        'web/courseleaf/wen',
        r"grep -hoP 'VERSION: \W\K[\d.]+(?=\W+$)' lib/wen.atj"),
    'formbuilder': GitProductWithVersionFile(
        'Formbuilder',
        'web/courseleaf/formbuilder',
        'clver.txt')
}
