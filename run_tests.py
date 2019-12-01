import pytest
from pathlib import Path

tests_dir = Path(__file__).parent.joinpath("tests")


if __name__ == "__main__":
    pytest.main([tests_dir.resolve(), "-v"])
