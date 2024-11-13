from pathlib import Path
from sys import argv
from os import makedirs
from enum import StrEnum

class Categories(StrEnum):
    Programming = "Programming"
    AI = "AI"
    Math = "Math"
    Database = "Database"
    Security = "Security"

def create_dirs(working_dir:Path):
    for category in Categories:
        makedirs(working_dir.joinpath(category))


def main(args):
    if len(args) != 2:
        raise ValueError("Incorrect Arguments. Format: <directory>")
    directory = Path(args[1])
    if not(directory.is_dir()):
        raise ValueError("Incorrect Arguments: Directory does not exist")
    create_dirs(directory)

if __name__ == "__main__":
    main(argv)
