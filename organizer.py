from pathlib import Path
from sys import argv
from os import makedirs, listdir, rename
from enum import StrEnum
import multiprocessing as mp

class Categories(StrEnum):
    Programming = "Programming"
    AI = "AI"
    Math = "Math"
    Database = "Database"
    Security = "Security"

def create_dirs(working_dir:Path):
    for category in Categories:
        makedirs(working_dir.joinpath(category), exist_ok=True)

def mock_task(file: Path):
    for catergory in Categories:
        if file.stem.lower() == catergory.lower():
            file.rename(file.parent.joinpath(catergory).joinpath(file.name))

def assign_processes(files: list[Path]):
    processes: list[mp.Process] = []
    for file in files:
        process = mp.Process(target=mock_task, args=(file, ))
        process.start()
        processes.append(process)
    return processes
        
def join_processes(processes:list[mp.Process]):
    for process in processes:
        process.join()

def main(args):
    if len(args) != 2:
        raise ValueError("Incorrect Arguments. Format: <directory>")
    directory = Path(args[1])
    if not(directory.is_dir()):
        raise ValueError("Incorrect Arguments: Directory does not exist")
    dir_contents = listdir(directory)
    pdf_files = [directory.joinpath(file) for file in dir_contents if Path(file).suffix == ".pdf"]
    if not pdf_files:
        raise ValueError("No PDF files found")
    create_dirs(directory)
    processes = assign_processes(pdf_files)
    join_processes(processes)

if __name__ == "__main__":
    argv.append("test")
    main(argv)