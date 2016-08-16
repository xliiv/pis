import json
import os
import tempfile
import unittest
from unittest import mock

from pis.config import config_default_path, read_config
from pis.config import init_user_config
from pis.lib import _get_links_from_pypi
from pis.lib import cd
from pis.lib import clone_repo
from pis.lib import source2pkg_name
from pis.lib import verify_pkg_dir
from pis.lib import url2vcses


#TODO:: mv to seperate file
SETUPPY_NAME_AS_STRING = '''
from setuptools import setup
setup(
    name="name_as_string",
)
'''

SETUPPY_NAME_AS_VAR = '''
from setuptools import setup
__name__ = 'name_as_dunder_name'

setup(
    name=__name__,
)
'''
SETUPPY_SETUP_AS_ATTRIBUTE = '''
import setuptools

setuptools.setup(
    name="setup_as_attribute",
)
'''


def _config():
    return read_config(config_default_path)


class TestCd(unittest.TestCase):
    def test_cd_works_ok(self):
        tmp_dir = tempfile.TemporaryDirectory()
        init_path = os.getcwd()
        with cd(tmp_dir.name):
            self.assertEqual(os.getcwd(), tmp_dir.name)
        self.assertEqual(init_path, init_path)


class TestUrl2VCSes(unittest.TestCase):
    def test_github_url_returns_url_returns_ok(self):
        url = "http://github.com/xliiv/pis"
        vcs = url2vcses(url, _config())
        self.assertEqual(len(vcs), 1)
        self.assertEqual(vcs[0].name, 'git')

    def test_bitbucket_url_returns_url_returns_ok(self):
        url = "http://bitbucket.org/xliiv/pis"
        vcs = url2vcses(url, _config())
        self.assertEqual(len(vcs), 2)
        self.assertEqual([v.name for v in vcs], ['git', 'hg'])


class TestGetLinksFromPypi(unittest.TestCase):
    def setUp(self):
        class ResponseStub:
            encoding = 'utf-8'
            content = ''.encode('utf-8')
        self.response = ResponseStub()
        self.url = 'https://pypi.python.org/pypi/pis'

    def test_url_found_when_plain_link(self):
        self.response.content = (
            " {} ".format(
                self.url,
            ).encode('utf-8')
        )
        found = _get_links_from_pypi(self.response)
        self.assertEqual([self.url], found)

    def test_url_found_when_link_in_html(self):
        self.response.content = (
            "<a href=\"{}\">naked boobs here!!</a> ".format(
                self.url,
            ).encode('utf-8')
        )
        found = _get_links_from_pypi(self.response)
        self.assertEqual([self.url], found)


class Source2PkgName(unittest.TestCase):
    def test_pkg_name_set_as_string(self):
        pkg_name = source2pkg_name(SETUPPY_NAME_AS_STRING)
        self.assertEqual(pkg_name, 'name_as_string')

    @unittest.skip(
        "needs more details, cos it can't be reproduced with current data"
    )
    def test_pkg_name_set_as_attribute(self):
        pkg_name = source2pkg_name(SETUPPY_NAME_AS_VAR)
        self.assertEqual(pkg_name, 'name_as_dunder_name')

    @unittest.skip("TODO")
    def test_pkg_name_set_when_full_path_import(self):
        #TODO:: this fails when setup.py uses setuptools.setup (instead of "setup(..)")
        pkg_name = source2pkg_name(SETUPPY_SETUP_AS_ATTRIBUTE)
        self.assertEqual(pkg_name, 'setup_as_attribute')


class TestVerifyPkgDir(unittest.TestCase):
    def _pkg_dir(self, pkg_name):
        return os.path.join(
            os.path.dirname(__file__), '_pkg_examples', pkg_name,
        )

    def test_return_true_when_name_matched(self):
        self.assertTrue(verify_pkg_dir(self._pkg_dir('ok_pkg'), 'ok_pkg'))

    def test_return_false_when_name_different(self):
        self.assertFalse(
            verify_pkg_dir(self._pkg_dir('other_pkg'), 'ok_pkg')
        )


class TestCloneRepo(unittest.TestCase):
    @mock.patch('pis.lib._clone_repo')
    def test_clone_repo_returns_true_when_cloned(self, mocked_fn):
        mocked_fn.return_value = True
        result = clone_repo('http://github.com/xliiv/pis', '.', _config())
        self.assertTrue(result)

    @mock.patch('pis.lib._clone_repo')
    def test_clone_repo_returns_false_when_failed(self, mocked_fn):
        mocked_fn.return_value = False
        result = clone_repo('http://github.com/xliiv/pis', '.', _config())
        self.assertFalse(result)


class TestConfigInit(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.absent_dir_name = tmp.name
        self.existing_dir = tempfile.TemporaryDirectory()
        self.config_name = 'user_conf.json'
        self.config_default = {
            'var': 'val'
        }

    def test_user_dir_is_created(self):
        init_user_config(
            self.absent_dir_name, self.config_name, self.config_default
        )
        self.assertTrue(os.path.exists(self.absent_dir_name))

    def test_user_config_is_created_when_config_dir_exists(self):
        init_user_config(
            self.existing_dir.name, self.config_name, self.config_default
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(self.existing_dir.name, self.config_name)
            )
        )

    def test_user_config_is_created_when_config_dir_is_absent(self):
        init_user_config(
            self.absent_dir_name, self.config_name, self.config_default
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(self.absent_dir_name, self.config_name)
            )
        )

    def test_created_user_config_is_as_default(self):
        init_user_config(
            self.absent_dir_name, self.config_name, self.config_default
        )
        with open(
            os.path.join(self.absent_dir_name, self.config_name)
        ) as conf:
            content = json.loads(conf.read())
        self.assertEqual(content, self.config_default)

    def test_stop_when_user_config_is_invalid_json(self):
        user_config = tempfile.NamedTemporaryFile()
        user_config.write('invalidjson'.encode('utf8'))
        with self.assertRaises(SystemExit):
            init_user_config(
                os.path.dirname(user_config.name),
                os.path.basename(user_config.name),
                {}
            )


@unittest.skip("TODO")
class TestSourceInstall(unittest.TestCase):
    def test_install_single_pkg_ok(self):
        import subprocess as subp
        path = '/home/xliiv/workspace/pis/pis/ok.sh'
        path2 = '/home/xliiv/workspace/pis/pis/bad.sh'
        print(path, path2)
        subp.check_call(['bash', 'tmp_dirpath', 'pis_execpath'])

    def test_install_many_pkg_ok(self):
        # source_install('pis', dir_path)
        pass

    def test_install_works_when_dir_passed(self):
        pass

    def test_install_raise_exception_when_dir_not_exists(self):
        pass
