from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
import autograder

def evaluate_proj1(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj1', accounts, 'dsa_proj1_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/simple.csv
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('carrot') < 0:
        return autograder.reject_submission(session,
            'I chose option 1 to load a CSV file, but the contents of that CSV file did not appear in the output. Did you print the CSV contents as described in step 8.l?',
            args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj2(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj2', accounts, 'dsa_proj2_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the stats correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/stats.csv
2

'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('9') < 0:
        return autograder.reject_submission(session,
            'I directed your program to load a dataset with 9 rows (not including the column names) and then print stats, but I could not find "9" anywhere in the output.',
        args, input, output
        )
    if output.find('3') < 0:
        return autograder.reject_submission(session,
            'I directed your program to load a dataset with 3 columns and then print stats, but I could not find "3" anywhere in the output.',
        args, input, output
        )
    if output.find('4') < 0:
        return autograder.reject_submission(session,
            'I directed your program to load a dataset with 4 unique values in one of the columns, but I could not find "4" anywhere in the output.',
        args, input, output
        )
    if output.find('5') < 0:
        return autograder.reject_submission(session,
            'I directed your program to load a dataset with 5 unique values in one of the columns, but I could not find "5" anywhere in the output.',
        args, input, output
        )
    if output.find('6') < 0:
        return autograder.reject_submission(session,
            'The most common value in one of the columns was "6", but I could not find "6" anywhere in the output.',
        args, input, output
        )
    if output.find('7') < 0:
        return autograder.reject_submission(session,
            'There were 7 unique values in one of the columns, but I could not find "7" anywhere in the output.',
        args, input, output
        )
    if output.find('apple') < 0:
        return autograder.reject_submission(session,
            'The most common value in one of the columns was "apple", but I could not find "apple" anywhere in the output of your program.',
        args, input, output
        )
    if output.find('red') < 0:
        return autograder.reject_submission(session,
            'The most common value in one of the columns was "red", but I could not find "red" anywhere in the output of your program.',
        args, input, output
        )
    if output.find('yellow') >= 0:
        return autograder.reject_submission(session,
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )
    if output.find('pumpkin') >= 0:
        return autograder.reject_submission(session,
            'It looks like your program still prints all the values in the dataset. It should not do that. See step 1.c.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj3(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj3', accounts, 'dsa_proj3_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the stats correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/simple.csv
2

'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('Color') < 0:
        return autograder.reject_submission(session,
            'I loaded a dataset with a column named "Color", and I printed stats, but the word "Color" did not occur in your output. Did you print all the column names?',
        args, input, output
        )
    if output.find('9') < 0:
        return autograder.reject_submission(session,
            'The max value in one of the columns was 9.0, but I did not find "9" in your output.',
        args, input, output
        )
    if output.find('5.714') < 0:
        return autograder.reject_submission(session,
            'The mean value in one of the columns was 5.71428, but I did not find this value in your output.',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj4(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj4', accounts, 'dsa_proj4_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it sorts a single column correctly
    try:
        args:List[str] = []
        input = '''1
/var/www/autograder/test_data/single_col.csv
4
0
5
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    terms_in_order = ['stuff', 'eat', 'swim', 'down', 'toothy', 'money', 'zebras']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(session,
                    'I sorted the only column, but the order came out wrong.',
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
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    terms_in_order = ['Food', 'doughnut', 'fish', 'apple', 'grapes', 'carrot', 'eggs', 'banana']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(session,
                    'I sorted by the second column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output
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
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    terms_in_order = ['Food', 'fish', 'eggs', 'apple', 'banana', 'doughnut']
    prev = -1
    for i in range(1, len(terms_in_order)):
        pos = output.find(terms_in_order[i])
        if i > 0:
            if prev >= pos:
                return autograder.reject_submission(session,
                    'I sorted by the third column, then checked the order in the first column, and the order was incorrect.',
                    args, input, output
                )
        prev = pos

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj5(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj5', accounts, 'dsa_proj5_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj6(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj6', accounts, 'dsa_proj6_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj7(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj7', accounts, 'dsa_proj7_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj8(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj8', accounts, 'dsa_proj8_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj9(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj9', accounts, 'dsa_proj9_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj10(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj10', accounts, 'dsa_proj10_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj11(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj11', accounts, 'dsa_proj11_submit.html')
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it prints the contents of a csv file when loaded
    try:
        args:List[str] = []
        input = '''1
xxx
'''
        output = autograder.run_submission(submission, args, input, False)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Could not find xxx',
        args, input, output
        )

    # Accept the submission
    return accept_submission(session, submission)

course_desc:Mapping[str,Any] = {
    'course_long': 'Data Structures & Algorithms',
    'course_short': 'dsa',
    'accounts': 'dsa_accounts.json',
    'projects': {
        'proj1': {
            'title': 'Project 1',
            'due_time': datetime(year=2024, month=1, day=29, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj1,
        },
        'proj2': {
            'title': 'Project 2',
            'due_time': datetime(year=2024, month=2, day=5, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj2,
        },
        'proj3': {
            'title': 'Project 3',
            'due_time': datetime(year=2024, month=2, day=12, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj3,
        },
        'proj4': {
            'title': 'Project 4',
            'due_time': datetime(year=2024, month=2, day=19, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj4,
        },
        'proj5': {
            'title': 'Project 5',
            'due_time': datetime(year=2024, month=3, day=4, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj5,
        },
        'proj6': {
            'title': 'Project 6',
            'due_time': datetime(year=2024, month=3, day=11, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj6,
        },
        'proj7': {
            'title': 'Project 7',
            'due_time': datetime(year=2024, month=3, day=25, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj7,
        },
        'proj8': {
            'title': 'Project 8',
            'due_time': datetime(year=2024, month=4, day=8, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj8,
        },
        'proj9': {
            'title': 'Project 9',
            'due_time': datetime(year=2024, month=4, day=15, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj9,
        },
        'proj10': {
            'title': 'Project 10',
            'due_time': datetime(year=2024, month=4, day=22, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj10,
        },
        'proj11': {
            'title': 'Project 11',
            'due_time': datetime(year=2024, month=4, day=29, hour=23, minute=59, second=59),
            'evaluator': evaluate_proj11,
        },
    },
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD DSA ACCOUNTS! Starting an empty file!!!')
    accounts = {}

def accept_submission(session:Session, submission:Mapping[str,Any]) -> Mapping[str,Any]:
    # Give the student credit
    account = submission['account']
    days_late = submission['days_late']
    title_clean = submission['title_clean']
    covered_days = min(days_late, account["toks"])
    account["toks"] -= covered_days
    days_late -= covered_days
    score = max(30, 100 - 3 * days_late)
    log(f'Passed: title={title_clean}, student={session.name}, days_late={days_late}, score={score}')
    account[title_clean] = score
    autograder.save_accounts(course_desc['accounts'], accounts)

    # Make an acceptance page
    return autograder.accept_submission(session, submission, days_late, covered_days, score)


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
