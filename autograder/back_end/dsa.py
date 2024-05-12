from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import log
from datetime import datetime
from threading import Lock
import autograder
import sys
import re
import os
import json
from session import Session

# Returns the first number in the string.
# Throws if there is not one.
def next_num(s:str) -> float:
    results = re.search(f'[-\d.]+[-+\d.e]*', s)
    if results:
        try:
            f = float(results.group())
        except:
            raise ValueError(f'"{results.group()}" looks like a number, but cannot be cast to a float')
        return f
    else:
        raise ValueError('No number found')

def submission_checks(submission:Mapping[str,Any]) -> None:
    # Check for forbidden files or folders
    forbidden_folders = [
        '.DS_Store',
        '.mypy_cache',
        '__pycache__',
        '.git',
        '.ipynb_checkpoints',
        '__MACOSX',
        '.settings',
        'backup',
        'data',
        'images',
        'pics',
    ]
    forbidden_extensions = [
        '', # usually compiled C++ apps
        '.bat', # windows batch files
        '.class', # compiled java
        '.dat',
        '.exe', 
        '.htm',
        '.html',
        '.ncb',
        '.pcb',
        '.pickle',
        '.pkl',
        '.o', # C++ object files
        '.obj', # C++ object files
        '.pdb',
        '.ps1', # powershell scripts
        '.suo', 
        '.tmp',
    ]
    file_count = 0
    base_path = submission['base_path']
    for path, folders, files in os.walk(base_path):
        for forbidden_folder in forbidden_folders:
            if forbidden_folder in folders:
                raise autograder.RejectSubmission(f'Your zip file contains a forbidden folder: "{forbidden_folder}". (Note that the zip command adds to an existing zip file. To remove a file it is necessary to delete your zip file and make a fresh one.)', [], '', '')
        for filename in files:
            _, ext = os.path.splitext(filename)
            for forbidden_extension in forbidden_extensions:
                if ext == forbidden_extension:
                    raise autograder.RejectSubmission(f'Your zip contains an unnecessary file: "{filename}". Please submit only your code and build script.', [], '', '')
            if ext == '.zip' and path != base_path:
                raise autograder.RejectSubmission(f'Your zip contains other zip files. Please submit only your code and build script.  (Note that the zip command adds to an existing zip file. To remove a file it is necessary to delete your zip file and make a fresh one.)', [], '', '')
            if os.stat(os.path.join(path, filename)).st_size > 2000000:
                msg =f'The file {filename} is too big. All files must be less than 2MB.'
                log(msg)
                raise autograder.RejectSubmission(msg, [], '', '')
        file_count += len(files)

    # Check that there are not too many files
    max_files = 50
    if file_count > max_files:
        raise autograder.RejectSubmission(f'Your zip file contains {file_count} files! Only {max_files} are allowed.  (Note that the zip command adds to an existing zip file. To remove files it is necessary to delete your zip file and make a fresh one.)', [], '', '')

def basic_checks(args:List[str], input:str, output:str) -> None:
    if output.find(': error: ') >= 0:
        raise autograder.RejectSubmission(
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        raise autograder.RejectSubmission(
            'It looks like an error was raised.',
            args, input, output
        )

def evaluate_hello(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''1
/var/www/autograder/test_data/simple.csv
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    if output.find('carrot') < 0:
        raise autograder.RejectSubmission(
            'I chose option 1 to load a CSV file, but the contents of that CSV file did not appear in the output. Did you print the CSV contents as described in step 8.l?',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_summarizing(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the stats correctly
    args:List[str] = []
    input = '''1
/var/www/autograder/test_data/stats.csv
2
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    if output.find('9') < 0:
        raise autograder.RejectSubmission(
            'I directed your program to load a dataset with 9 rows (not including the column names) and then print stats, but I could not find "9" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('3') < 0:
        raise autograder.RejectSubmission(
            'I directed your program to load a dataset with 3 columns and then print stats, but I could not find "3" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('4') < 0:
        raise autograder.RejectSubmission(
            'I directed your program to load a dataset with 4 unique values in one of the columns, but I could not find "4" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('5') < 0:
        raise autograder.RejectSubmission(
            'I directed your program to load a dataset with 5 unique values in one of the columns, but I could not find "5" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('6') < 0:
        raise autograder.RejectSubmission(
            'The most common value in one of the columns was "6", but I could not find "6" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('7') < 0:
        raise autograder.RejectSubmission(
            'There were 7 unique values in one of the columns, but I could not find "7" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('apple') < 0:
        raise autograder.RejectSubmission(
            'The most common value in one of the columns was "apple", but I could not find "apple" anywhere in the output of your program.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('red') < 0:
        raise autograder.RejectSubmission(
            'The most common value in one of the columns was "red", but I could not find "red" anywhere in the output of your program.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('yellow') >= 0:
        raise autograder.RejectSubmission(
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )
    if output.find('pumpkin') >= 0:
        raise autograder.RejectSubmission(
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_correlations(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the stats correctly
    args:List[str] = []
    input = '''1
/var/www/autograder/test_data/simple.csv
2
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    if output.find('Color') < 0:
        raise autograder.RejectSubmission(
            'I loaded a dataset with a column named "Color", and I printed stats, but the word "Color" did not occur in your output. Did you print all the column names?',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if output.find('9') < 0:
        raise autograder.RejectSubmission(
            'The max value in one of the columns was 9.0, but I did not find "9" in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if output.find('5.714') < 0:
        raise autograder.RejectSubmission(
            'The mean value in one of the columns was 5.71428, but I did not find this value in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_sorting(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it sorts a single column correctly
    args:List[str] = []
    input = '''1
/var/www/autograder/test_data/single_col.csv
4
0
5
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    terms_in_order = ['stuff', 'eat', 'swim', 'down', 'toothy', 'money', 'zebras']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                raise autograder.RejectSubmission(
                    f'Expected the order to be sorted according to the smart_compare custom comparator. Got some other order.',
                    args, input, output
                )
        prev = pos

    # Test 2: See if it sorts by the second column correctly
    args = []
    input = '''1
/var/www/autograder/test_data/simple.csv
4
1
5
0
'''
    output = autograder.run_submission(submission, args, input, False)
    terms_in_order = ['Food', 'doughnut', 'fish', 'apple', 'grapes', 'carrot', 'eggs', 'banana']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                raise autograder.RejectSubmission(
                    'I sorted by the second column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
                )
        prev = pos

    # Test 3: See if it sorts by the third column correctly
    args = []
    input = '''1
/var/www/autograder/test_data/simple.csv
4
2
5
0
'''
    output = autograder.run_submission(submission, args, input, False)
    terms_in_order = ['Food', 'fish', 'eggs', 'apple', 'banana', 'doughnut']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                raise autograder.RejectSubmission(
                    'I sorted by the third column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
                )
        prev = pos

    # Accept the submission
    return accept_submission(submission)

def evaluate_binary_search(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: Do a query
    args:List[str] = []
    input = '''6
/var/www/autograder/test_data/simple.csv
7
0
dog
fish
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    brown_index = output.find('brown')
    if brown_index < 0:
        raise autograder.RejectSubmission(
            'Expected the row with doughnut to appear in the output',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    white_index = output.find('white')
    if white_index < 0:
        raise autograder.RejectSubmission(
            'Expected the row with eggs to appear in the output',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if white_index < brown_index:
        raise autograder.RejectSubmission(
            'Expected doughnut to come before eggs',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    fish_index = output.find('fish')
    if fish_index >= 0:
        raise autograder.RejectSubmission(
            'Did not expect the fish row to be in the output. You are supposed to stop before the end row.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    carrot_index = output.find('carrot')
    if carrot_index >= 0:
        raise autograder.RejectSubmission(
            'Did not expect the carrot row to be in the output. Carrot comes before doughnut.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Test 2: Do another query
    args = []
    input = '''6
/var/www/autograder/test_data/simple.csv
7
2
2
4
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    carrot_pos = output.find('carrot')
    if carrot_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the carrot row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    fish_pos = output.find('fish')
    if fish_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the fish row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    eggs_pos = output.find('eggs')
    if eggs_pos >= 0:
        raise autograder.RejectSubmission(
            'Did not expect the eggs row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_attr_ranking(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''1
/var/www/autograder/test_data/corr.csv
8
4
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    attr0_pos = output.rfind('random1')
    attr1_pos = output.rfind('predictive')
    attr2_pos = output.rfind('random2')
    attr3_pos = output.rfind('random3')
    if attr0_pos < 0 or attr1_pos < 0 or attr2_pos < 0 or attr3_pos < 0:
        raise autograder.RejectSubmission(
            'One or more of the column names did not appear in your output. You are supposed to drop each column, and print its name as you do.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/corr.csv')
        )
    if attr1_pos < attr0_pos or attr1_pos < attr2_pos or attr1_pos < attr3_pos:
        raise autograder.RejectSubmission(
            '"predictive" should have been the last column to be dropped (because it is the most predictive of the "target" column). However, it looks like one of the other column names occurs later in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/corr.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_pca(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''9
/var/www/autograder/test_data/pca.csv
10
0
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    zero_colon_pos = output.rfind('0: ')
    five_colon_pos = output.rfind('5: ')
    six_colon_pos = output.rfind('6: ')
    seven_colon_pos = output.rfind('7: ')
    eight_colon_pos = output.rfind('8: ')
    if eight_colon_pos >= 0:
        raise autograder.RejectSubmission(
            'There should only be 8 dimensions in the Numpy representation of this data, but your output indicates that it found more than 8 principal components.',
        args, input, output
        )
    if seven_colon_pos < 0:
        raise autograder.RejectSubmission(
            'There should be 8 dimensions in the Numpy representation of this data, but your output indicates that it found fewer than 8 principal components.',
        args, input, output
        )
    try:
        zero_eig = next_num(output[zero_colon_pos + 3:])
        five_eig = next_num(output[five_colon_pos + 3:])
        six_eig = next_num(output[six_colon_pos + 3:])
    except ValueError:
        raise autograder.RejectSubmission(
            'Expected a number after "0:", "5:", and "6:".',
        args, input, output
        )
    if zero_eig > 50.:
        raise autograder.RejectSubmission(
            'Your first root-eigenvalue is too big. Did you center and standardize the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig > 5.:
        raise autograder.RejectSubmission(
            'Your first root-eigenvalue is too big. Did you center the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig > 1.6:
        raise autograder.RejectSubmission(
            'Your first root-eigenvalue is too big. Did you standardize the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig < 1.1:
        raise autograder.RejectSubmission(
            'Your first root-eigenvalue is too small.',
        args, input, output
        )
    if five_eig < 0.8 or five_eig > 1.2:
        raise autograder.RejectSubmission(
            'Your fifth root-eigenvalue is incorrect.',
        args, input, output
        )
    if six_eig > 0.2:
        raise autograder.RejectSubmission(
            'Your sixth root-eigenvalue is too large.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_jupyter(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)
    
    # Find the Jupyter notebook
    if not 'folder' in submission:
        raise autograder.RejectSubmission(
            'Internal error: Expected "folder" in the submission.',
            args, input, output
        )
    notebook_filename = ''
    for path, folders, files in os.walk(submission['folder']):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext == '.ipynb':
                notebook_filename = os.path.join(path, filename)
                break

    # Load the Jupyter notebook
    try:
        with open(notebook_filename, 'r') as f:
            notebook_content = f.read()
    except:
        raise autograder.RejectSubmission(
            f'Unable to parse {notebook_filename}',
            args, input, output
        )

    # Check the notebook for some key parts
    if not notebook_content.find('markdown') >= 0:
        raise autograder.RejectSubmission(
            f'Expected a markdown cell in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.normal') >= 0:
        raise autograder.RejectSubmission(
            f'Expected random values to be drawn from a normal distribution in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.scatter') >= 0:
        raise autograder.RejectSubmission(
            f'Expected a scatter plot in the notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.bar') >= 0:
        raise autograder.RejectSubmission(
            f'Expected a bar chart in the notebook: {notebook_filename}',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_pandas(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)

    # Find the Jupyter notebook
    if not 'folder' in submission:
        raise autograder.RejectSubmission(
            'Internal error: Expected "folder" in the submission.',
            args, input, output
        )
    notebook_filename = ''
    for path, folders, files in os.walk(submission['folder']):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext == '.ipynb':
                notebook_filename = os.path.join(path, filename)
                break

    # Load the Jupyter notebook
    try:
        with open(notebook_filename, 'r') as f:
            notebook_content = f.read()
    except:
        raise autograder.RejectSubmission(
            f'Unable to parse {notebook_filename}',
            args, input, output
        )

    # Check the notebook for some key parts
    if not notebook_content.find('markdown') >= 0:
        raise autograder.RejectSubmission(
            f'Expected at least one markdown cell in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('pandas') >= 0:
        raise autograder.RejectSubmission(
            f'Expected pandas in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.hist') >= 0:
        raise autograder.RejectSubmission(
            f'Expected a histogram plot in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('Series') >= 0:
        raise autograder.RejectSubmission(
            f'Expected Series operations in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('DataFrame') >= 0:
        raise autograder.RejectSubmission(
            f'Expected DataFrame operations in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.iloc') >= 0:
        raise autograder.RejectSubmission(
            f'Expected .iloc operations in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.loc') >= 0:
        raise autograder.RejectSubmission(
            f'Expected .loc operations in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.drop') >= 0:
        raise autograder.RejectSubmission(
            f'Expected a .drop operation in your notebook: {notebook_filename}',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_data_mining(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1: See if it prints the contents of a csv file when loaded
    args:List[str] = []
    input = '''
'''
    output = autograder.run_submission(submission, args, input, False)
    basic_checks(args, input, output)

    # Find the Jupyter notebook
    if not 'folder' in submission:
        raise autograder.RejectSubmission(
            'Internal error: Expected "folder" in the submission.',
            args, input, output
        )
    notebook_filename = ''
    for path, folders, files in os.walk(submission['folder']):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext == '.ipynb':
                notebook_filename = os.path.join(path, filename)
                break

    # Load the Jupyter notebook
    try:
        with open(notebook_filename, 'r') as f:
            notebook_content = f.read()
    except:
        raise autograder.RejectSubmission(
            f'Unable to parse {notebook_filename}',
            args, input, output
        )

    # Check the notebook for some key parts
    if not notebook_content.find('markdown') >= 0:
        raise autograder.RejectSubmission(
            f'Expected markdown cells in your notebook: {notebook_filename}. You are supposed to document your work, not just do it.',
            args, input, output
        )
    if not notebook_content.find('matplotlib') >= 0:
        raise autograder.RejectSubmission(
            f'Expected to find matplotlib in your notebook: {notebook_filename}. Surely you must want to show a plot of something!',
            args, input, output
        )
    if not notebook_content.find('numpy') >= 0:
        raise autograder.RejectSubmission(
            f'Expected numpy in your notebook: {notebook_filename}. You are supposed to demonstrate all the things we learned this semester. Surely, that must include something from numpy.',
            args, input, output
        )
    if not notebook_content.find('pandas') >= 0:
        raise autograder.RejectSubmission(
            f'Expected pandas in your notebook: {notebook_filename}. You are supposed to demonstrate all the things we learned this semester. Surely, that must include something from Pandas.',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

course_desc:Mapping[str,Any] = {
    'course_long': 'Data Structures & Algorithms',
    'course_short': 'dsa',
    'projects': {
        'hello': {
            'title': 'Project 1',
            'due_time': datetime(year=2024, month=1, day=29, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_hello,
        },
        'summarizing': {
            'title': 'Project 2',
            'due_time': datetime(year=2024, month=2, day=5, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_summarizing,
        },
        'correlations': {
            'title': 'Project 3',
            'due_time': datetime(year=2024, month=2, day=13, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_correlations,
        },
        'sorting': {
            'title': 'Project 4',
            'due_time': datetime(year=2024, month=2, day=20, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_sorting,
        },
        'midterm1': {
            'title': 'Midterm 1',
            'due_time': datetime(year=2024, month=2, day=26, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 90,
        },
        'binary_search': {
            'title': 'Project 5',
            'due_time': datetime(year=2024, month=3, day=7, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_binary_search,
        },
        'attr_ranking': {
            'title': 'Project 6',
            'due_time': datetime(year=2024, month=3, day=26, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_attr_ranking,
        },
        'pca': {
            'title': 'Project 7',
            'due_time': datetime(year=2024, month=4, day=2, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_pca,
        },
        'midterm2': {
            'title': 'Midterm 2',
            'due_time': datetime(year=2024, month=4, day=9, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 75,
        },
        'jupyter': {
            'title': 'Project 8',
            'due_time': datetime(year=2024, month=4, day=16, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_jupyter,
        },
        'pandas': {
            'title': 'Project 9',
            'due_time': datetime(year=2024, month=4, day=23, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_pandas,
        },
        'data_mining': {
            'title': 'Project 10',
            'due_time': datetime(year=2024, month=4, day=30, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_data_mining,
        },
        'final': {
            'title': 'Final exam',
            'due_time': datetime(year=2024, month=5, day=7, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 92,
        },
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc)
except:
    print(f'*** FAILED TO LOAD {course_desc["course_short"]} ACCOUNTS! Starting an empty file!!!')
    accounts = {}


accept_lock = Lock()

def accept_submission(submission:Mapping[str,Any]) -> Mapping[str,Any]:
    # Give the student credit
    with accept_lock:
        account = submission['account']
        days_late = submission['days_late']
        proj_id = submission['proj_id']
        covered_days = min(days_late, account["toks"])
        days_late -= covered_days
        score = max(30, 100 - 3 * days_late)
        if not (proj_id in account): # to protect from multiple simultaneous accepts
            log(f'Passed: title={proj_id}, days_late={days_late}, score={score}')
            account[proj_id] = score
            account["toks"] -= covered_days
            autograder.save_accounts(course_desc, accounts)

        # Make an acceptance page
        return autograder.accept_submission(submission, days_late, covered_days, score)

def view_scores_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.view_scores_page(params, session, f'{course_desc["course_short"]}_view_scores.html', accounts, course_desc)

def admin_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_admin_page(params, session, f'{course_desc["course_short"]}_admin.html', accounts, course_desc)

# To initialize the accounts at the start of a semester
# (1) Delete the accounts file (or else this will just add to it)
# (2) Paste a list of student names below.
#     (You can get a list of student names from UAConnect,
#      click on the icon to export to a spreadsheet,
#      then copy the names column and paste below.)
# (3) Run this file directly.
#     Example:
#       cd ../front_end
#       python3 ../back_end/thisfile.py
# 
# To add a missing student, just skip step 1, and put only that
# one student name below. It will add that student to the accounts.
def initialize_accounts() -> None:
    try:
        accounts:Dict[str,Any] = autograder.load_accounts(course_desc)
    except:
        accounts = {}
    autograder.save_accounts(course_desc, accounts)

if __name__ == "__main__":
    initialize_accounts()
