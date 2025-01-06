import os
import re
import socket
import subprocess

def get_path():
    return os.getcwd()

def get_username():
    return os.getlogin()

def get_hostname():
    return socket.gethostname()

def get_dev_hostname():
    hostname = get_hostname()
    if re.match(r'^build\d+\.leepfrog\.com$', hostname):
        return hostname.replace('build', 'dev')
    else:
        raise Exception('Expected a hostname in the format build#.leepfrog.com, where # is 1 or more digits; got "' + hostname + '" instead')

def get_shell_output(cmd: str, cwd=None, stderr=subprocess.DEVNULL, executable='/bin/bash') -> str:
    #shell_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, shell=True, cwd=cwd, executable=executable, check=True)
    #shell_res.check_returncode()

    #shell_res = subprocess.run(cmd, shell=True, capture_output=True, check=True, cwd=cwd, executable=executable)
    # compatibility for python 3.6:
    shell_res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, cwd=cwd, executable=executable)

    shell_res.check_returncode()
    return shell_res.stdout.decode('utf-8')
