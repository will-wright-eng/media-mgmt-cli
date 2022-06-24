"""
media management CLI - config setup
- export environment varibles
- setup dot directory at $HOME
- grab configs from AWS secrets
- os.environ.get("HOME", "Does not exist")
- use builtin python configparser "import configparser"

- add note to environment variable calls --> "environment variable {} not found, run `mmgmt configure` to setup"

`mmgmt configure`
- check environment variables
- check for .mmgmt dorectory in HOME --> .mmgmt/config
- mkdir $HOME/.mmgmt
- touch $HOME/.mmgmt/config
"""

import os
import pathlib
import configparser


class ConfigHandler:
    def __init__(self, project_name):
        p = pathlib.Path.home()
        self.home_path = p
        self.config_path = p / ".config" / project_name
        self.config_file_path = self.config_path / "config"

        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file_path):
            self.config.read(self.config_file_path)
            # print("-- config file exists --")
            # print(self.config.defaults())

    def export_configs(self):
        # export configs as environment variables
        for key, val in self.config.defaults().items():
            if key is not None:
                os.environ[key.upper()] = val

    def print_configs(self):
        for key, val in self.config.defaults().items():
            if key is not None:
                print(key.upper(), (20 - int(len(key))) * " ", val)

    def write_config_file(self):
        # rewrite config file
        with open(self.config_file_path, "w") as configfile:
            self.config.write(configfile)

    def create_file_and_dir(self):
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.config_file_path.touch()

    def config_file_input(self, config_dict: dict, section: str = "DEFAULT"):
        """
        example:
        config['DEFAULT'] = {'ServerAliveInterval': '45',
                          'Compression': 'yes',
                          'CompressionLevel': '8',
                          }
        """
        self.config[section] = config_dict

    def write_config_file_from_dict(self, config_dict: dict):
        self.config_file_input(config_dict)
        self.write_config_file()

    def get_configs(self):
        if os.path.isfile(self.config_file_path):
            return self.config.defaults()
        else:
            return None

    def check_config_exists(self):
        return os.path.isfile(self.config_file_path)


config_handler = ConfigHandler(project_name="media_mgmt_cli")


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def create_res_dict_from_envrc():
    files = find_all(".envrc", "../.")
    projects = ["media_mgmt_cli", "twl_app"]
    res = {}
    for file_path, project_name in zip(files, projects):
        tmp_res = {}
        with open(file_path, "r") as file:
            tmp_lines = file.readlines()
            for pos, line in enumerate(tmp_lines):
                tmp_var = line.replace("\n", "").replace("export ", "").split("=")
                if "KEY" in tmp_var[0]:
                    pass
                else:
                    tmp_res[tmp_var[0]] = tmp_var[1]
        res[project_name] = tmp_res
    return res


def create_secret_from_dict(project_name, secrets_dict):
    secrets_prefix = "projects/dev"
    secret_name = os.path.join(secrets_prefix, project_name)
    secret_string = json.dumps(secrets_dict)
    return aws.create_secret(secret_string, secret_name)


# for project_name in projects:
#     create_secret_from_dict(project_name, secrets_dict=res[project_name])
