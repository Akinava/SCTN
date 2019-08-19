# FIXME put all variable in to config.json
# parce and put variable as local
import json
import os


config_file = 'src/config.json'
hosts = {}


def import_config():
    with open(config_file, 'r') as cfg_file:
        config = json.loads(cfg_file.read())
        for k, v in config.items():
            globals()[k] = v



def import_hosts():
    if os.path.isfile(hosts_file):
        with open(hosts_file, 'r') as f:
            try:
                hosts = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                pass


def save_hosts():
    with open(hosts_file, 'w') as f:
        f.write(json.dumps(hosts, indent=2))


import_config()
import_hosts()
