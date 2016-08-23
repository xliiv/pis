import collections
import json
import logging
import os
import sys

from pip._vendor import requests


try:
    from json.decoder import JSONDecodeError
except ImportError:
    # python < 3.5
    JSONDecodeError = ValueError


log = logging.getLogger(__file__)

#TODO:: rm config_  prefix
config_encoding = 'utf8'
config_filename = 'config.json'
config_default_path = os.path.join(
    os.path.dirname(__file__), config_filename
)
config_user_dir = os.path.join(os.path.expanduser('~'), '.' + __package__)
config_user_path = os.path.join(config_user_dir, config_filename)

latest_config_url = 'https://raw.githubusercontent.com/xliiv/pis/master/pis/config.json'


def merge_dicts(dikt, dikt2):
    for k, v in dikt2.items():
        if (
            k in dikt and
            isinstance(dikt[k], dict) and
            isinstance(dikt2[k], collections.Mapping)
        ):
            merge_dicts(dikt[k], dikt2[k])
        else:
            dikt[k] = dikt2[k]


def init_user_config(config_dir, config_name, config_default):
    config_user_path = os.path.join(config_dir, config_name)
    try:
        read_config(config_user_path)
    except FileNotFoundError:
        try:
            os.mkdir(config_dir)
        except FileExistsError:
            pass
        write_config(config_user_path, config_default)
    except JSONDecodeError:
        log.error(
            "Config file ({}) includes invalid JSON".format(config_user_path)
        )
        sys.exit(1)


def read_config(path):
    #TODO:: merge apps with user config?
    with open(path) as config_file:
        return json.loads(config_file.read())


def write_config(path, config_dict, encoding=config_encoding):
    with open(path, 'wb') as config_file:
        config_file.write(json.dumps(config_dict).encode(encoding))


def download_latest_config(latest_config_url):
    response = requests.get(latest_config_url)
    #TODO: error handling
    assert response.status_code == 200, "Couldn't get latest json"
    return json.loads(response.content.decode())


def with_latest_config(latest_config_url, config_path):
    user_config = read_config(config_path)
    latest_config = download_latest_config(latest_config_url)
    merge_dicts(user_config, latest_config)
    return user_config


init_user_config(
    config_user_dir, config_filename, read_config(config_default_path)
)
