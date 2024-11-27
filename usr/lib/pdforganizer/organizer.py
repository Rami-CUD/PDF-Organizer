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

#Constant variable specifying the location of the installed library files
LIB_DIR = Path("/", "usr", "lib", "pdforganizer")

#Enum class for each category
class Categories(StrEnum):
    Programming = "Programming"
    AI = "AI"
    Math = "Math"
    Database = "Database"
    Security = "Security"
    Other = "Other"

#Helper function to extract json contents into a python dictionary
def get_json_file_contents(json_file_name):
    with open(LIB_DIR.joinpath(json_file_name), "r") as json_file:
        return json.load(json_file)

#Goes through the categories specified in the Enum and makes a directory for each one
def create_dirs(working_dir:Path):
    for category in Categories:
        makedirs(working_dir.joinpath(category), exist_ok=True)

#Read all keywords present in a file
def get_file_keywords(file: Path) -> set[str]:
    #Initialize a string builder object to store all the keywords
    #This is similar to intializing an empty string and adding to it, but it's more efficient
    keywords = StringIO()
    #Add the name of the file to the keywords
    keywords.write(file.stem.lower())
    
    #Try to read the pdf file. In case it's empty, simply return the current keywords (just the file name)
    try:
        reader = PdfReader(file)
    except EmptyFileError:
        return keywords.getvalue()
    
    #Check the metadata for a "keywords" and "Title" field
    #If present, add them to the keywords string
    if key := "/keywords" in reader.metadata:
        keywords.write(str(reader.metadata.get(key)).lower())
    
    if key := "/Title" in reader.metadata: 
        keywords.write(str(reader.metadata.get(key)).lower())
    
    #Try to read the first page and extract all of it's text to add to the keywords
    #In case this fails, simply return the current keywords
    try:
        first_page = reader.pages[0]
        keywords.write(first_page.extract_text().lower())
    except IndexError:
        pass
    finally:
        return keywords.getvalue()
    


#Main function that is run by every process that categorizes one file
#It gets the file category using another function, then moves the file into that category's directory.
#It also keeps track of that assignment by puting it in the shared queue
def put_file_in_category_folder(file: Path, shared_counter:mp.Queue):
    category:Categories = get_file_category(file)
    file.rename(file.parent.joinpath(category).joinpath(file.name))
    shared_counter.put((file,category))

#Determine the category of a given file
def get_file_category(file):
    #Read the categorical keywords from the json file as a dict
    categorical_keywords = get_json_file_contents("keywords.json")
    
    #Extract all keywords from the file to compare with the categorical keywords
    file_keywords = get_file_keywords(file)
    
    #A dictionary to keep track of how many keyword matches were found for each category
    category_scores = defaultdict(int)
    
    #For every category except Other, loop through all it's categorical keywords and check how
    #many times they are present in the file. 
    for category in Categories:
        if category == Categories.Other:
            continue
        for keyword in categorical_keywords[category]:
            #This regular expressions searches for all words seperated by either a whitespace character
            #or an underscore
            if matches := re.findall(fr"(?:\b|_){keyword}(?:\b|_)", file_keywords):                
                category_scores[category] += len(matches)
    
    #If by the end category scores is empty, it means no keyword matches were found, and the category
    #is set to other
    if not category_scores:
        return Categories.Other
    
    #Otherwise, we return the category with the maximum number of matches
    maximum_score_category = max(category_scores, key=category_scores.get)
    return maximum_score_category

#Searches through every PDF file and assign a process to categorize it. Returns a list of the processes
def assign_processes(files: list[Path], shared_counter: mp.Queue) -> list[mp.Process]:
    processes: list[mp.Process] = []
    for file in files:
        process = mp.Process(target=put_file_in_category_folder, args=(file, shared_counter))
        process.start()
        processes.append(process)
    return processes

#The parent process loops through every child process in the list and waits for it to finish  
#Similar to C's wait()
def join_processes(processes:list[mp.Process]):
    for process in processes:
        process.join()

#A class that is desgined to keep track of all the category assignments at the end.
# Since these assignments need to be extracted from the queue individually
# the class keeps track of both the integer count of each category as well as each
# individual assignment. This just means that the count doesn't have to be calculated manually
# for each category at run time. 
class AssignmentsTracker:
    #Initialize dict to keep track of how many pdf files were assigned to each category. Ex:
    #{"Database": 10, "AI": 4}
    #Initialize set that contains the tuples of each indivial file assignments. Ex:
    # { ("file1.pdf", Category("Math")) } 
    #This is used for calculating the correctness score
    def __init__(self) -> None:
        self.category_counter = defaultdict(int)
        self.file_assignments = set()

    #A helper function that both updates the counter and adds the assignment to the set
    def add_assignment(self, file:Path, category:Categories):
        self.category_counter[category] += 1
        self.file_assignments.add((file.stem, category))

#Dequeue all the elements in the shared queue and add the assignments to the AssignmentsTracker object
def count_categories(shared_counter: mp.Queue) -> AssignmentsTracker:
    assignments = AssignmentsTracker()
    for _ in range(shared_counter.qsize()):
        file, category = shared_counter.get()
        assignments.add_assignment(file, category)
    return assignments

#Creates a reports.txt file in the specified directory that shows the percentage of each category and
#the correcteness score.
def generate_report(directory:Path, fileCount:int, assignments: AssignmentsTracker, correctness=False):
    #Initialize list of lines to be printed
    lines = ["Analysis Report:\n", "----------------\n"]
    
    #For every category get the amount of files that were assigned to it and divide it by the total file count
    for category in Categories:
        category_count = assignments.category_counter[category]
        percentage = round(category_count/fileCount * 100)
        lines.append(f"{category}: {percentage}%\n")
    
    # If correctness needs to be calculated, read the correct pre-defined assignments and compare
    # them to the assignments made by the algorithm
    if correctness:
        lines.append("\n")
        correct_assignments:dict = get_json_file_contents("correct_categorizations.json")
        correct_set = {(file, Categories(category)) for file, category in correct_assignments.items()}
        incorrect_assignments = len(assignments.file_assignments.difference(correct_set))
        correctness_score = fileCount - incorrect_assignments
        correctness_percentage = round(correctness_score/fileCount * 100)
        lines.append(f"Correctness Score: {correctness_percentage}%\n")

    #Write the report.txt file in the correct directory
    with open(directory.joinpath("report.txt"), "w") as report:
        report.writelines(lines)

#Main function that runs all other procedures
def main(args):
    #Check that the correct amount of arguments was passed
    if len(args) != 4:
        raise ValueError("Incorrect Number of Arguments")
    #Extract the PDF directory and the report directory from the arguments
    directory = Path(args[1])
    report_dir = Path(args[2])
    
    #Ensure the given PDF directory is a directory and that it has PDFs
    if not(directory.is_dir()):
        raise ValueError("Incorrect Arguments: Directory does not exist")
    if not(report_dir.is_dir()):
        raise ValueError("Incorrect Arguments: Report directory does not exist")

    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        raise ValueError("No PDF files found")
    
    #Create the directories for all the categories
    create_dirs(directory)
    #Create a shared queue in shared memory so the processes can keep count of their category assignments
    shared_counter: mp.Queue[tuple[Path,Categories]] = mp.Queue()
    
    #Assign the processes
    processes = assign_processes(pdf_files, shared_counter)
    
    #Wait for all the child processes to finish
    join_processes(processes)
    
    #Count all the category assignments and store them in an Assignments Tracker datatype
    assignments: AssignmentsTracker = count_categories(shared_counter)
    
    #Reads final argument given to script that determines whether it will generate a correctness score.
    generate_correctness = bool(args[3])
    
    #Generate the report
    generate_report(report_dir, len(pdf_files), assignments, generate_correctness)

#Check that the file is being run as a script
if __name__ == "__main__":
    main(argv)