from pathlib import Path
from sys import argv
from os import makedirs
from enum import StrEnum
import multiprocessing as mp
from pypdf import PdfReader
from pypdf.errors import EmptyFileError
import json
import re
from collections import defaultdict
from io import StringIO

LIB_DIR = Path("/", "usr", "lib", "pdforganizer")

class Categories(StrEnum):
    Programming = "Programming"
    AI = "AI"
    Math = "Math"
    Database = "Database"
    Security = "Security"
    Other = "Other"

def get_json_file_contents(json_file_name):
    with open(LIB_DIR.joinpath(json_file_name), "r") as json_file:
        return json.load(json_file)

def create_dirs(working_dir:Path):
    for category in Categories:
        makedirs(working_dir.joinpath(category), exist_ok=True)

def get_file_keywords(file: Path) -> set[str]:
    keywords = StringIO()
    keywords.write(file.stem.lower())
    try:
        reader = PdfReader(file)
    except EmptyFileError:
        return keywords.getvalue()
    
    if key := "/keywords" in reader.metadata:
        keywords.write(str(reader.metadata.get(key)).lower())
    
    if key := "/Title" in reader.metadata: 
        keywords.write(str(reader.metadata.get(key)).lower())
    
    try:
        first_page = reader.pages[0]
        keywords.write(first_page.extract_text().lower())
    except IndexError:
        pass
    finally:
        return keywords.getvalue()
    



def put_file_in_category_folder(file: Path, shared_counter:mp.Queue):
    category:Categories = get_file_category(file)
    file.rename(file.parent.joinpath(category).joinpath(file.name))
    shared_counter.put((file,category))

def get_file_category(file):
    categorical_keywords = get_json_file_contents("keywords.json")
    file_keywords = get_file_keywords(file)
    category_scores = defaultdict(int)
    for category in Categories:
        if category == Categories.Other:
            continue
        for keyword in categorical_keywords[category]:
            if matches := re.findall(fr"(?:\b|_){keyword}(?:\b|_)", file_keywords):                
                category_scores[category] += len(matches)

    if not category_scores:
        return Categories.Other
    maximum_score_category = max(category_scores, key=category_scores.get)
    return maximum_score_category

def assign_processes(files: list[Path], shared_counter: mp.Queue):
    processes: list[mp.Process] = []
    for file in files:
        process = mp.Process(target=put_file_in_category_folder, args=(file, shared_counter))
        process.start()
        processes.append(process)
    return processes
        
def join_processes(processes:list[mp.Process]):
    for process in processes:
        process.join()

class AssignmentsTracker:
    def __init__(self) -> None:
        self.category_counter = defaultdict(int)
        self.file_assignments = set()

    def add_assignment(self, file:Path, category:Categories):
        self.category_counter[category] += 1
        self.file_assignments.add((file.stem, category))

def count_categories(shared_counter: mp.Queue) -> AssignmentsTracker:
    assignments = AssignmentsTracker()
    for _ in range(shared_counter.qsize()):
        file, category = shared_counter.get()
        assignments.add_assignment(file, category)
    return assignments

def generate_report(directory:Path, fileCount:int, assignments: AssignmentsTracker, correctness=False):
    lines = ["Analysis Report:\n", "----------------\n"]
    for category in Categories:
        category_count = assignments.category_counter[category]
        percentage = round(category_count/fileCount * 100)
        lines.append(f"{category}: {percentage}%\n")
    
    if correctness:
        lines.append("\n")
        correct_assignments:dict = get_json_file_contents("correct_categorizations.json")
        correct_set = {(file, Categories(category)) for file, category in correct_assignments.items()}
        incorrect_assignments = len(assignments.file_assignments.difference(correct_set))
        correctness_score = fileCount - incorrect_assignments
        correctness_percentage = round(correctness_score/fileCount * 100)
        lines.append(f"Correctness Score: {correctness_percentage}%\n")

    
    with open(directory.joinpath("report.txt"), "w") as report:
        report.writelines(lines)


def main(args):
    if len(args) != 4:
        raise ValueError("Incorrect Number of Arguments")
    directory = Path(args[1])
    report_dir = Path(args[2])
    if not(directory.is_dir()):
        raise ValueError("Incorrect Arguments: Directory does not exist")
    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        raise ValueError("No PDF files found")
    create_dirs(directory)
    shared_counter: mp.Queue[tuple[Path,Categories]] = mp.Queue()
    processes = assign_processes(pdf_files, shared_counter)
    join_processes(processes)
    assignments: AssignmentsTracker = count_categories(shared_counter)
    generate_correctness = bool(args[3])
    generate_report(report_dir, len(pdf_files), assignments, generate_correctness)

if __name__ == "__main__":
    main(argv)