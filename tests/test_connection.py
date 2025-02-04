from tempfile import NamedTemporaryFile
from textwrap import dedent


def test_new_connection_can_be_added(runner, snapshot):
    with NamedTemporaryFile("w+", suffix=".toml") as tmp_file:
        result = runner.invoke(
            [
                "--config-file",
                tmp_file.name,
                "connection",
                "add",
                "--connection-name",
                "conn1",
                "--username",
                "user1",
                "--password",
                "password1",
                "--account",
                "account1",
            ]
        )
        content = tmp_file.read()
    assert result.exit_code == 0, result.output
    assert content == snapshot


def test_new_connection_add_prompt_handles_default_values(runner, snapshot):
    with NamedTemporaryFile("w+", suffix=".toml") as tmp_file:
        result = runner.invoke(
            [
                "--config-file",
                tmp_file.name,
                "connection",
                "add",
            ],
            input="connName\naccName\nuserName",
        )
        content = tmp_file.read()
    assert result.exit_code == 0, result.output
    assert content == snapshot


def test_new_connection_add_prompt_handles_prompt_override(runner, snapshot):
    with NamedTemporaryFile("w+", suffix=".toml") as tmp_file:
        result = runner.invoke(
            [
                "--config-file",
                tmp_file.name,
                "connection",
                "add",
            ],
            input="connName\naccName\nuserName\ndbName",
        )
        content = tmp_file.read()
    assert result.exit_code == 0, result.output
    assert content == snapshot


def test_fails_if_existing_connection(runner):
    with NamedTemporaryFile("w+", suffix=".toml") as tmp_file:
        tmp_file.write(
            dedent(
                """\
        [connections]
        [connections.conn2]
        username = "foo"
        """
            )
        )
        tmp_file.flush()
        result = runner.invoke(
            [
                "--config-file",
                tmp_file.name,
                "connection",
                "add",
                "--connection-name",
                "conn2",
                "--username",
                "user1",
                "--password",
                "password1",
                "--account",
                "account1",
            ]
        )
    assert result.exit_code == 1, result.output
    assert "Connection conn2 already exists  " in result.output
