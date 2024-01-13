from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
import autograder

course_desc:Mapping[str,Any] = {
    'course': 'Data Structures & Algorithms',
    'accounts': 'dsa_accounts.json',
    'projects': {
        'proj1': {
            "title": "Project 1",
            "due_time": datetime(year=2023, month=11, day=28, hour=23, minute=59, second=59),
        },
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD ACCOUNTS! Starting an empty file!!!')
    accounts = {}



def dsa_proj1_receive(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc['projects']['proj1'], accounts)
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])
    account = submission['account']
    days_late = submission['days_late']
    start_folder = submission['folder']
    title_clean = submission['title_clean']

    # Run some tests
    try:
        args = ['aaa', 'bbb', 'ccc']
        input = '''Aloysius
8'''
        output = autograder.run_submission(start_folder, args, input)
    except Exception as e:
        return autograder.make_submission_error_page(str(e), session)
    expected = '''The arguments passed in were:
arg 1 = aaa
arg 2 = bbb
arg 3 = ccc
Hello, what is your name?
> And what is your favorite number?
> Ok, Aloysius, I will count to 8 (with zero-indexed values):
0 ah-ah-ah!
1 ah-ah-ah!
2 ah-ah-ah!
3 ah-ah-ah!
4 ah-ah-ah!
5 ah-ah-ah!
6 ah-ah-ah!
7 ah-ah-ah!
Thanks for stopping by. Have a nice day!

'''

    p:List[str] = []
    autograder.page_start(p, session)
    if output == expected:
        covered_days = min(days_late, account["toks"])
        account["toks"] -= covered_days
        days_late -= covered_days
        score = max(30, 100 - 3 * days_late)
        log(f'Passed: title={title_clean}, student={session.name}, days_late={days_late}, score={score}')
        account[title_clean] = score
        autograder.save_accounts(course_desc['accounts'], accounts)
        p.append('<font color="green">Your submission passed all tests! Your assignment is complete. You have tentatively been given full credit.')
        p.append('(However, the grade is not final until the grader looks at it.)</font>')
    else:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        if len(args) > 0:
            p.append(f'Args passed in: <pre class="code">{" ".join(args)}</pre><br><br>')
        if len(input) > 0:
            p.append(f'Input fed in: <pre class="code">{input}</pre><br><br>')
        p.append(f'Output: <pre class="code">{output}</pre><br><br>')
        p.append(f'Expected output: <pre class="code">{expected}</pre><br><br>')
        p.append('Please fix the issue and resubmit.')
    autograder.page_end(p)
    return {
        'content': ''.join(p),
    }


def dsa_proj1_submit(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_submission_page(
        params,
        session,
        course_desc['course'],
        course_desc['projects']['proj1'],
        accounts,
        course_desc['accounts'],
        'dsa_proj1_submit.html',
        'dsa_proj1_receive.html',
    )


def log_out(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_log_out_page(params, session)

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