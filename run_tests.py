import pytest
from pathlib import Path
import os

tests_dir = Path(__file__).parent.joinpath("tests")


os.chdir(tests_dir.parent.resolve())

if __name__ == "__main__":
    pytest.main([tests_dir.resolve(), "-v"])
