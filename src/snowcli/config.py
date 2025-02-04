from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Any, Dict

import tomlkit
from tomlkit import dump, table, TOMLDocument
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import Table
from tomlkit.container import Container
import logging

from snowcli.exception import MissingConfiguration, UnsupportedConfigSectionTypeError
from snowflake.connector.constants import CONFIG_FILE
from snowflake.connector.config_manager import ConfigManager


log = logging.getLogger(__name__)


class CliConfigManager(ConfigManager):
    def __init__(self, file_path: Path = CONFIG_FILE):
        super().__init__(name="SNOWCLI_PARSER", file_path=file_path)
        self._add_options()

    def from_context(self, config_path_override: Optional[Path]):
        if config_path_override:
            self.file_path = config_path_override
        if not self.file_path.exists():
            self._initialise_config()
        self.read_config()

    def get_section(self, *path) -> dict:
        section = self._find_section(*path)
        if type(section) is Container:
            return {
                s: self._merge_section_with_env(section[s], *path, s) for s in section
            }
        elif type(section) is Table:
            return self._merge_section_with_env(section, *path)
        raise UnsupportedConfigSectionTypeError(type(section))

    def section_exists(self, *path) -> bool:
        try:
            self._find_section(*path)
            return True
        except NonExistentKey:
            return False

    def get(self, *path, key: str, default: Optional[Any] = None) -> Any:
        """Looks for given key under nested path in toml file."""
        env_variable = self._get_env_value(*path, key=key)
        if env_variable:
            return env_variable
        try:
            return self.get_section(*path)[key]
        except NonExistentKey:
            if default:
                return default
            raise

    def get_connection(self, connection_name: str) -> dict:
        try:
            return self.get_section("connections", connection_name)
        except NonExistentKey:
            raise MissingConfiguration(
                f"Connection {connection_name} is not configured"
            )

    def add_connection(self, name: str, parameters: dict):
        if not self.section_exists("connections"):
            self._initialize_connection_section()
        self._find_section("connections").add(name, parameters)
        self._dump_config()

    def _add_options(self):
        self.add_option(
            name="options",
            parse_str=tomlkit.parse,
        )
        self.add_option(
            name="connections",
            parse_str=tomlkit.parse,
        )

    def _find_section(self, *path) -> TOMLDocument:
        section = self
        idx = 0
        while idx < len(path):
            section = section[path[idx]]
            idx += 1
        return section

    def _merge_section_with_env(self, section: Table, *path) -> Dict[str, str]:
        section_copy = section.copy()
        env_variables = self._get_envs_for_path(*path)
        section_copy.update(env_variables)
        return section_copy

    def _get_env_value(self, *path, key: str):
        env_variable_name = (
            "SNOWFLAKE_" + "_".join(p.upper() for p in path) + f"_{key.upper()}"
        )
        return os.environ.get(env_variable_name)

    def _get_envs_for_path(self, *path) -> dict:
        env_variables_prefix = "SNOWFLAKE_" + "_".join(p.upper() for p in path)
        return {
            k.replace(f"{env_variables_prefix}_", "").lower(): os.environ[k]
            for k in os.environ.keys()
            if k.startswith(env_variables_prefix)
        }

    def _initialize_connection_section(self):
        self.conf_file_cache = TOMLDocument()
        self.conf_file_cache.append("connections", table())

    def _initialise_config(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._initialize_connection_section()
        self._dump_config()
        log.info(f"Created Snowflake configuration file at {cli_config.file_path}")

    def _dump_config(self):
        with open(self.file_path, "w+") as fh:
            dump(self.conf_file_cache, fh)


def config_init(config_file: Path):
    """
    Initializes the app configuration. Config provided via cli flag takes precedence.
    If config file does not exist we create an empty one.
    """
    cli_config.from_context(config_path_override=config_file)


cli_config: CliConfigManager = CliConfigManager()  # type: ignore
