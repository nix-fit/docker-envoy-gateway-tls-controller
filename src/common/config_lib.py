import os
from pathlib import Path

import yaml

APP_CONFIG_DIR = os.environ.get(
    "APP_CONFIG_DIR",
    Path("config"),
)
APP_CONFIG_NAME = os.environ.get("APP_CONFIG_NAME", "config")


def get_yaml_contents(filename: str):
    if not filename:
        raise FileNotFoundError("Filename must not be empty.")
    home_dir = os.environ.get("HOME")
    path = f"{home_dir}/{APP_CONFIG_DIR}/{filename}.yaml"
    if not Path(path).is_file():
        raise FileNotFoundError(f"No file located at {path}")
    tmpl: str = open(path, "rt").read()
    return tmpl


class Config:
    def __init__(self):
        self.config: dict = self._load_config()

    def _load_config(self):
        file_string = get_yaml_contents(filename=APP_CONFIG_NAME)
        config = yaml.safe_load(file_string)
        return config


app_config = Config()
