"""Pytest config."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest add option."""
    parser.addoption("--files-directory", action="store")


@pytest.fixture
def files_directory(request: pytest.FixtureRequest) -> str:
    """Pytest fixture files-directory command line option."""
    return request.config.getoption("--files-directory")
