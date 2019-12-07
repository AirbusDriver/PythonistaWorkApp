import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug', help='run CLI tool with DEBUG_MODE=TRUE', 
    action='store_true', default=False
    )

args = parser.parse_args()

DEBUG_MODE = args.debug

log_level = logging.DEBUG if DEBUG_MODE else logging.ERROR

logger = logging.getLogger("")
logger.handlers.clear()

console_handler = logging.StreamHandler()

log_formatter = logging.Formatter(
    '[{asctime!s}] [{name!s}] [{levelname!s}]: {message!s}', style='{'
    )
console_handler.setFormatter(log_formatter)

logger.addHandler(console_handler)

logger.setLevel(log_level)


# set up loggers before calling modules which may do further formatting

from winds.shell import WindShell

shell = WindShell()
shell.cmdloop()
