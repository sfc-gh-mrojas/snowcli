import io
import logging
import os
import shutil
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from snowcli.cli.snowpark import package

from tests.test_data import test_data


class TestPackage:
    @pytest.mark.parametrize(
        "argument",
        [
            (
                "snowflake-connector-python",
                "Package snowflake-connector-python is available on the Snowflake anaconda channel.",
                "snowcli.cli.snowpark.package",
            ),
            (
                "some-weird-package-we-dont-know",
                "not found in Snowflake anaconda channel...",
                "snowcli.utils",
            ),
        ],
    )
    @patch("tests.test_package.package.utils.requests")
    def test_package_lookup(self, mock_requests, caplog, argument, monkeypatch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = test_data.anaconda_response
        mock_requests.get.return_value = mock_response

        monkeypatch.setattr("sys.stdin", io.StringIO("N"))

        with caplog.at_level(logging.DEBUG, logger=argument[2]):
            result = package.package_lookup(argument[0], install_packages=True)

        assert caplog.text
        assert argument[1] in caplog.text

    @patch("tests.test_package.package.utils.requests")
    def test_package_create(self, mock_requests, caplog, packages_directory):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = test_data.anaconda_response
        mock_requests.get.return_value = mock_response

        with caplog.at_level(logging.DEBUG, logger="snowcli.cli.snowpark.package"):
            result = package.package_create("totally-awesome-package")

        assert (
            f"Package totally-awesome-package.zip created. You can now upload it to a stage (`snow package upload -f totally-awesome-package.zip -s packages`) and reference it in your procedure or function."
            in caplog.text
        )
        os.remove("totally-awesome-package.zip")

    @pytest.fixture
    def packages_directory(self):
        path = os.path.join(os.getcwd(), ".packages")
        os.mkdir(path)
        yield path
