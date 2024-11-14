from pathlib import Path
from sys import argv
from os import makedirs, listdir, rename
from enum import StrEnum
import multiprocessing as mp
from PyPDF2 import PdfReader
from PyPDF2.errors import EmptyFileError
import json
import re

class Categories(StrEnum):
    Programming = "Programming"
    AI = "AI"
    Math = "Math"
    Database = "Database"
    Security = "Security"
    Other = "Other"

def get_categorical_keywords() -> dict[str, list]:
    with open("keywords.json", "r") as json_file:
        return json.load(json_file)

def create_dirs(working_dir:Path):
    for category in Categories:
        makedirs(working_dir.joinpath(category), exist_ok=True)

def get_file_keywords(file: Path) -> set[str]:
    keywords = set()
    WHITESPACE_OR_UNDERSCORE = re.compile("\W+|_")
    try:
        reader = PdfReader(file)
    except EmptyFileError:
        keywords = set(WHITESPACE_OR_UNDERSCORE.split(file.stem.lower()))
        return keywords
    
    if key := "/keywords" in reader.metadata:
        extracted_metadata = str(reader.metadata.get(key)).lower()
        split_metadata = set(extracted_metadata.split(","))
        keywords = keywords.union(split_metadata)
    
    if key := "/Title" in reader.metadata: 
        keywords = keywords.union(set(str(reader.metadata.get(key)).lower().split()))
    
    first_page = reader.pages[0]
    first_page_keywords = set(first_page.extract_text().lower().split())
    keywords = keywords.union(first_page_keywords)
    
    return keywords
    



def categorize_file(file: Path):
    category:Categories = get_file_category(file)
    file.rename(file.parent.joinpath(category).joinpath(file.name))

def get_file_category(file):
    categorical_keywords = get_categorical_keywords()
    file_keywords = get_file_keywords(file)
    category_scores = {}
    for category in Categories:
        if category == Categories.Other:
            continue
        present_keywords = file_keywords.intersection(set(categorical_keywords[category]))
        category_scores[category] = len(present_keywords)
    maximum_score_category = max(category_scores, key=category_scores.get)
    return Categories(maximum_score_category) if category_scores[maximum_score_category] > 0 else Categories.Other

def assign_processes(files: list[Path]):
    processes: list[mp.Process] = []
    for file in files:
        process = mp.Process(target=categorize_file, args=(file, ))
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
    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        raise ValueError("No PDF files found")
    create_dirs(directory)
    processes = assign_processes(pdf_files)
    join_processes(processes)

if __name__ == "__main__":
    main(argv)