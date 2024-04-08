from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
from threading import Lock
import autograder
import re
import os
import json

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

def evaluate_proj1(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/simple.csv
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('carrot') < 0:
        return autograder.reject_submission(submission,
            'I chose option 1 to load a CSV file, but the contents of that CSV file did not appear in the output. Did you print the CSV contents as described in step 8.l?',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj2(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the stats correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/stats.csv
2
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('9') < 0:
        return autograder.reject_submission(submission,
            'I directed your program to load a dataset with 9 rows (not including the column names) and then print stats, but I could not find "9" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('3') < 0:
        return autograder.reject_submission(submission,
            'I directed your program to load a dataset with 3 columns and then print stats, but I could not find "3" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('4') < 0:
        return autograder.reject_submission(submission,
            'I directed your program to load a dataset with 4 unique values in one of the columns, but I could not find "4" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('5') < 0:
        return autograder.reject_submission(submission,
            'I directed your program to load a dataset with 5 unique values in one of the columns, but I could not find "5" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('6') < 0:
        return autograder.reject_submission(submission,
            'The most common value in one of the columns was "6", but I could not find "6" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('7') < 0:
        return autograder.reject_submission(submission,
            'There were 7 unique values in one of the columns, but I could not find "7" anywhere in the output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('apple') < 0:
        return autograder.reject_submission(submission,
            'The most common value in one of the columns was "apple", but I could not find "apple" anywhere in the output of your program.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('red') < 0:
        return autograder.reject_submission(submission,
            'The most common value in one of the columns was "red", but I could not find "red" anywhere in the output of your program.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/stats.csv')
        )
    if output.find('yellow') >= 0:
        return autograder.reject_submission(submission,
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )
    if output.find('pumpkin') >= 0:
        return autograder.reject_submission(submission,
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj3(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the stats correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/simple.csv
2
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('Color') < 0:
        return autograder.reject_submission(submission,
            'I loaded a dataset with a column named "Color", and I printed stats, but the word "Color" did not occur in your output. Did you print all the column names?',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if output.find('9') < 0:
        return autograder.reject_submission(submission,
            'The max value in one of the columns was 9.0, but I did not find "9" in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if output.find('5.714') < 0:
        return autograder.reject_submission(submission,
            'The mean value in one of the columns was 5.71428, but I did not find this value in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj4(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it sorts a single column correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/single_col.csv
4
0
5
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    terms_in_order = ['stuff', 'eat', 'swim', 'down', 'toothy', 'money', 'zebras']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(submission,
                    f'Expected the order to be sorted according to the smart_compare custom comparator. Got some other order.',
                    args, input, output
                )
        prev = pos

    # Test 2: See if it sorts by the second column correctly
    try:
        args = []
        input = '''1
/var/www/autograder/test_data/simple.csv
4
1
5
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    terms_in_order = ['Food', 'doughnut', 'fish', 'apple', 'grapes', 'carrot', 'eggs', 'banana']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(submission,
                    'I sorted by the second column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
                )
        prev = pos

    # Test 3: See if it sorts by the third column correctly
    try:
        args = []
        input = '''1
/var/www/autograder/test_data/simple.csv
4
2
5
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    terms_in_order = ['Food', 'fish', 'eggs', 'apple', 'banana', 'doughnut']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(submission,
                    'I sorted by the third column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
                )
        prev = pos

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj5(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: Do a query
    try:
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
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    brown_index = output.find('brown')
    if brown_index < 0:
        return autograder.reject_submission(submission,
            'Expected the row with doughnut to appear in the output',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    white_index = output.find('white')
    if white_index < 0:
        return autograder.reject_submission(submission,
            'Expected the row with eggs to appear in the output',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    if white_index < brown_index:
        return autograder.reject_submission(submission,
            'Expected doughnut to come before eggs',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    fish_index = output.find('fish')
    if fish_index >= 0:
        return autograder.reject_submission(submission,
            'Did not expect the fish row to be in the output. You are supposed to stop before the end row.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    carrot_index = output.find('carrot')
    if carrot_index >= 0:
        return autograder.reject_submission(submission,
            'Did not expect the carrot row to be in the output. Carrot comes before doughnut.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Test 2: Do another query
    try:
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
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    carrot_pos = output.find('carrot')
    if carrot_pos < 0:
        return autograder.reject_submission(submission,
            'Expected the carrot row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    fish_pos = output.find('fish')
    if fish_pos < 0:
        return autograder.reject_submission(submission,
            'Expected the fish row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    eggs_pos = output.find('eggs')
    if eggs_pos >= 0:
        return autograder.reject_submission(submission,
            'Did not expect the eggs row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj6(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/corr.csv
8
4
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/corr.csv')
        )
    attr0_pos = output.rfind('random1')
    attr1_pos = output.rfind('predictive')
    attr2_pos = output.rfind('random2')
    attr3_pos = output.rfind('random3')
    if attr0_pos < 0 or attr1_pos < 0 or attr2_pos < 0 or attr3_pos < 0:
        return autograder.reject_submission(submission,
            'One or more of the column names did not appear in your output. You are supposed to drop each column, and print its name as you do.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/corr.csv')
        )
    if attr1_pos < attr0_pos or attr1_pos < attr2_pos or attr1_pos < attr3_pos:
        return autograder.reject_submission(submission,
            '"predictive" should have been the last column to be dropped (because it is the most predictive of the "target" column). However, it looks like one of the other column names occurs later in your output.',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/corr.csv')
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj7(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''9
/var/www/autograder/test_data/pca.csv
10
0
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    zero_colon_pos = output.rfind('0: ')
    five_colon_pos = output.rfind('5: ')
    six_colon_pos = output.rfind('6: ')
    seven_colon_pos = output.rfind('7: ')
    eight_colon_pos = output.rfind('8: ')
    if eight_colon_pos >= 0:
        return autograder.reject_submission(submission,
            'There should only be 8 dimensions in the Numpy representation of this data, but your output indicates that it found more than 8 principal components.',
        args, input, output
        )
    if seven_colon_pos < 0:
        return autograder.reject_submission(submission,
            'There should be 8 dimensions in the Numpy representation of this data, but your output indicates that it found fewer than 8 principal components.',
        args, input, output
        )
    zero_eig = next_num(output[zero_colon_pos + 3:])
    five_eig = next_num(output[five_colon_pos + 3:])
    six_eig = next_num(output[six_colon_pos + 3:])
    if zero_eig > 50.:
        return autograder.reject_submission(submission,
            'Your first root-eigenvalue is too big. Did you center and standardize the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig > 5.:
        return autograder.reject_submission(submission,
            'Your first root-eigenvalue is too big. Did you center the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig > 1.6:
        return autograder.reject_submission(submission,
            'Your first root-eigenvalue is too big. Did you standardize the columns before computing eigenvalues?',
        args, input, output
        )
    if zero_eig < 1.1:
        return autograder.reject_submission(submission,
            'Your first root-eigenvalue is too small.',
        args, input, output
        )
    if five_eig < 0.8 or five_eig > 1.2:
        return autograder.reject_submission(submission,
            'Your fifth root-eigenvalue is incorrect.',
        args, input, output
        )
    if six_eig > 0.2:
        return autograder.reject_submission(submission,
            'Your sixth root-eigenvalue is too large.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj8(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if not 'folder' in submission:
        return autograder.reject_submission(submission,
            'Internal error: Expected "folder" in the submission.',
            args, input, output
        )
    
    # Find the Jupyter notebook
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
        return autograder.reject_submission(submission,
            f'Unable to parse {notebook_filename}',
            args, input, output
        )

    # Check the notebook for some key parts
    if not notebook_content.find('markdown') >= 0:
        return autograder.reject_submission(submission,
            f'Expected a markdown cell in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.normal') >= 0:
        return autograder.reject_submission(submission,
            f'Expected random values to be drawn from a normal distribution in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('matplotlib inline') >= 0:
        return autograder.reject_submission(submission,
            f'Expected inline plots in your notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.scatter') >= 0:
        return autograder.reject_submission(submission,
            f'Expected a scatter plot in the notebook: {notebook_filename}',
            args, input, output
        )
    if not notebook_content.find('.bar') >= 0:
        return autograder.reject_submission(submission,
            f'Expected a bar chart in the notebook: {notebook_filename}',
            args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj9(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(submission,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj10(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(submission,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj11(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(submission, str(e))
    if output.find(': error: ') >= 0:
        return autograder.reject_submission(submission,
            'It looks like there are errors.',
            args, input, output
        )
    if output.find('Traceback (most') >= 0:
        return autograder.reject_submission(submission,
            'It looks like an error was raised.',
            args, input, output
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(submission,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(submission)

course_desc:Mapping[str,Any] = {
    'course_long': 'Data Structures & Algorithms',
    'course_short': 'dsa',
    'accounts': 'dsa_accounts.json',
    'projects': {
        'proj1': {
            'title': 'Project 1',
            'due_time': datetime(year=2024, month=1, day=29, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj1,
        },
        'proj2': {
            'title': 'Project 2',
            'due_time': datetime(year=2024, month=2, day=5, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj2,
        },
        'proj3': {
            'title': 'Project 3',
            'due_time': datetime(year=2024, month=2, day=13, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj3,
        },
        'proj4': {
            'title': 'Project 4',
            'due_time': datetime(year=2024, month=2, day=20, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj4,
        },
        'midterm1': {
            'title': 'Midterm 1',
            'due_time': datetime(year=2024, month=2, day=26, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 90,
        },
        'proj5': {
            'title': 'Project 5',
            'due_time': datetime(year=2024, month=3, day=7, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj5,
        },
        'proj6': {
            'title': 'Project 6',
            'due_time': datetime(year=2024, month=3, day=26, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj6,
        },
        'proj7': {
            'title': 'Project 7',
            'due_time': datetime(year=2024, month=4, day=2, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj7,
        },
        'proj8': {
            'title': 'Project 8',
            'due_time': datetime(year=2024, month=4, day=16, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj8,
        },
        'proj9': {
            'title': 'Project 9',
            'due_time': datetime(year=2024, month=4, day=23, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj9,
        },
        'proj10': {
            'title': 'Project 10',
            'due_time': datetime(year=2024, month=4, day=30, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj10,
        },
    },
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD DSA ACCOUNTS! Starting an empty file!!!')
    accounts = {}


accept_lock = Lock()

def accept_submission(submission:Mapping[str,Any]) -> Mapping[str,Any]:
    # Give the student credit
    with accept_lock:
        account = submission['account']
        days_late = submission['days_late']
        title_clean = submission['title_clean']
        covered_days = min(days_late, account["toks"])
        days_late -= covered_days
        score = max(30, 100 - 3 * days_late)
        if not (title_clean in account): # to protect from multiple simultaneous accepts
            log(f'Passed: title={title_clean}, days_late={days_late}, score={score}')
            account[title_clean] = score
            account["toks"] -= covered_days
            autograder.save_accounts(course_desc['accounts'], accounts)

        # Make an acceptance page
        return autograder.accept_submission(submission, days_late, covered_days, score)

def view_scores_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.view_scores_page(params, session, 'dsa_view_scores.html', accounts, course_desc)

def admin_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_admin_page(params, session, 'dsa_admin.html', accounts, course_desc)

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
    student_list = '''Armstrong,William Michael
Beaman,Brynn A
Ben Aissa,Erije
Blinn,David
Brown,Myli Elizabeth
Do,Victoria Quynhanh
Donnell-Lonon,William J
Ehrisman,Luke Daniel
Endacott,Jackson J
Evers,Jameson
Gallemore,Alicia Bella Rose
Galvan Londono,Andres Felipe
Green,Jackson D
Groom,Kieran J
Harriman,Craig Hunter
Helser,Dillon L
Herman,Emma Grace
Hill,Brady William
Hoang,Amy
Howerton,Carlie Sue
Husong,Breck T
Jones,Lucas Patrick
Lanter,Zachary David
Latz,Devin T
Laurie,Jacob Matthew
Lawlis,Sarah Lydia
Le,Kaitlyn Ngoc-Lan
Levin,Lawson Cotton Andrew
Magnus,Stephen Bruce
Maurer,Connor S
Mayden,Lauren Elizabeth
McBride,Sarah Lynn
McGowen,Joseph P
Mooneyham,Abby C
Morris,Coy R
Packan,Trevor M
Partridge,Colin Julian
Pinto Avelar,Aura Lizbeth
Rivera,Gabriel Sebastian
Robinson,William Carl
Scharf,Noa Lynne
Schoenhals,Emmett Easton
Shortt,Jordan Janell
Stepanova,Daria
Thomas,Katherine Page
Thompson,Avery Ann
Trout,Samuel J
Tutka,Benjamin Z
Walters,Ruth E
Watts,Annabelle Elise
Wilhite,Kaydence Naomi
'''
    names = student_list.split('\n')
    try:
        accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
    except:
        accounts = {}
    autograder.add_students(names, accounts)
    autograder.save_accounts(course_desc['accounts'], accounts)

if __name__ == "__main__":
    initialize_accounts()
