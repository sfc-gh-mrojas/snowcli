from click.exceptions import ClickException


class EnvironmentVariableNotFoundError(ClickException):
    def __init__(self, env_variable_name: str):
        super().__init__(f"Environment variable {env_variable_name} not found")


class MissingConfiguration(ClickException):
    pass


class InvalidConnectionConfiguration(ClickException):
    def format_message(self):
        return f"Invalid connection configuration. {self.message}"


class SnowflakeConnectionError(ClickException):
    def __init__(self, snowflake_err: Exception):
        super().__init__(f"Could not connect to Snowflake. Reason: {snowflake_err}")


class UnsupportedConfigSectionTypeError(Exception):
    def __init__(self, section_type: type):
        super().__init__(f"Unsupported configuration section type {section_type}")
