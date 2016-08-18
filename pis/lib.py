import ast
import contextlib
import glob
import logging
import os
import pip
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

from pip._vendor import requests
from pip.utils import call_subprocess
from pip.vcs import vcs



logger = logging.getLogger(__name__)

#TODO: user info
#TODO: release with readme, with examples of use, and rm todos from setup.py etc.
#TODO: cli arg dst_path is repo itself this is not what i meant, fix it
#TODO: respect versions by tags or branches
#TODO: docstrings
#TODO: resolve all TODOs (including those from test file)
#TODO: got installed flask=master, then install flask==0.9, it could wipe your whole dir
#       - stop running when dir is found


def _clone_repo(vcs, dst_path):
    try:
        print(vcs.obtain(dst_path))
    except pip.exceptions.InstallationError:
        result = False
    else:
        result = True
    return result


def clone_repo(repo_url, dst_path, config):
    vcses = url2vcses(repo_url, config)
    for VCSClass in vcses:
        full_url = '+'.join([VCSClass.name, repo_url])
        vcs = VCSClass(full_url)
        if _clone_repo(vcs, dst_path):
            return True
        else:
            continue
    return False


@contextlib.contextmanager
def cd(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def url2vcses(url, config):
    vcses = []
    parsed = urlparse(url)
    vcs_names = config['repo_hosts2vcses'].get(parsed.netloc, [])
    for name in vcs_names:
        for registered_vcs in vcs.backends:
            if registered_vcs.name == name:
                vcses.append(registered_vcs)
    return vcses


def source2pkg_name(setuppy_source):
    tree = ast.parse(setuppy_source)
    fl = FuncLister()
    fl.visit(tree)
    return fl.pkg_name


class FuncLister(ast.NodeVisitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pkg_name = None

    def visit_Call(self, node):
        #TODO:: this failes when setup.py uses setuptools.setup (instead of "setup(..)")
        if getattr(node.func, 'id', '') == 'setup':
            for keyword in node.keywords:
                if keyword.arg == 'name':
                    if isinstance(keyword.value, ast.Str):
                        # handle case: name='pkg_name'
                        self.pkg_name = keyword.value.s
                    elif (
                        # handle case: name=__name__
                        isinstance(keyword.value, ast.Attribute) and
                        keyword.value.attr == '__name__'
                    ):
                        self.pkg_name = keyword.value.value.id
                    else:
                        self.pkg_name = None
        self.generic_visit(node)


def verify_pkg_dir(pkg_dir, pkg_name):
    setup_py_path = os.path.join(pkg_dir, 'setup.py')
    try:
        with open(setup_py_path) as f:
            setuppy_source = f.read()
    except FileNotFoundError:
        is_pkg_dir = False
    else:
        cloned_pkg_name = source2pkg_name(setuppy_source)
        # pypi ignores case, so `pis` and `PIS` is the same package
        is_pkg_dir = cloned_pkg_name.lower() == pkg_name.lower()
    return is_pkg_dir


def _get_links_from_pypi(response, default_encoding='utf-8'):
    content = response.content.decode(response.encoding or default_encoding)
    matcher = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')  # noqa
    return matcher.findall(content)


def get_links_from_pypi(pkg_homepage_url, default_encoding):
    """
    Get all links from `pkg_homepage`.
    """
    response = requests.get(pkg_homepage_url)
    return _get_links_from_pypi(response, default_encoding)


def install_pkg(pkg_dir):
    cmd = "pip install -e {}".format(pkg_dir).split()
    subprocess.check_call(cmd)


#
# DIRT STUFF BEGINS
#

def filter_urls(urls, ok_values):
    #TODO:: write tests
    new_urls = []
    for url in urls:
        for netloc in ok_values:
            if netloc in url:
                new_urls.append(url)
    return new_urls


def source_install(pkges_list, dir_path, config):
    founds = {}
    for pkg_name in pkges_list:
        url = config['pkg_name2repo_url'].get(pkg_name, None)
        if url:
            urls = [url]
        else:
            pkg_homepage = config['pypi_url'].format(pkg_name=pkg_name)
            urls = get_links_from_pypi(pkg_homepage, 'utf-8')
            urls = filter_urls(urls, config['repo_hosts2vcses'].keys())
        for url in urls:
            if clone_repo(repo_url=url, dst_path=pkg_name, config=config):
                if verify_pkg_dir(pkg_dir=pkg_name, pkg_name=pkg_name):
                    install_pkg(pkg_dir=pkg_name)
                    founds[pkg_name] = url
                    break
                else:
                    shutil.rmtree(pkg_dir)
    return founds
