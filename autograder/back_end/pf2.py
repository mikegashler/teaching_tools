from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
import autograder

course_desc:Mapping[str,Any] = {
    'course': 'Programming Foundations II',
    'accounts': 'pf2_accounts.json',
    'projects': {
        'proj1': {
            "title": "Project 1",
            "due_time": datetime(year=2024, month=1, day=22, hour=23, minute=59, second=59),
        },
        'proj2': {
            "title": "Project 2",
            "due_time": datetime(year=2024, month=1, day=29, hour=23, minute=59, second=59),
        },
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD ACCOUNTS! Starting an empty file!!!')
    accounts = {}



def pf2_proj1_receive(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc['projects']['proj1'], accounts)
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])
    account = submission['account']
    days_late = submission['days_late']
    start_folder = submission['folder']
    title_clean = submission['title_clean']

    # Test 1: See if it produces the exactly correct output
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
    if output != expected:
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

    # Accept the submission
    covered_days = min(days_late, account["toks"])
    account["toks"] -= covered_days
    days_late -= covered_days
    score = max(30, 100 - 3 * days_late)
    log(f'Passed: title={title_clean}, student={session.name}, days_late={days_late}, score={score}')
    account[title_clean] = score
    autograder.save_accounts(course_desc['accounts'], accounts)
    p.append('<font color="green">Your submission passed all tests! Your assignment is complete. You have tentatively been given full credit.')
    p.append('(However, the grade is not final until the grader looks at it.)</font>')
    autograder.page_end(p)
    return {
        'content': ''.join(p),
    }

def pf2_proj2_receive(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc['projects']['proj2'], accounts)
    if not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])
    account = submission['account']
    days_late = submission['days_late']
    start_folder = submission['folder']
    title_clean = submission['title_clean']

    p:List[str] = []
    autograder.page_start(p, session)

    # Test 1: not debug mode, short list
    try:
        args:List[str] = []
        input = '''alpha
beta
charlie
delta
epsilon
'''
        output = autograder.run_submission(start_folder, args, input)
    except Exception as e:
        return autograder.make_submission_error_page(str(e), session)
    if output.find('debug mode') >= 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('I did not pass in the "debug" flag, but it still ran in debug mode!')        
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }
    if output.find('delta') < 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('The words in the lexicon were not displayed when not in debug mode.')        
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }

    # Test 2: debug mode, long list
    try:
        args = ['debug']
        input = '''alpha
beta
charlie
delta
epsilon
frank
george
harry
indigo
jackson
kappa
llama
money
nubile
oscar
petrify
quirky
rascal
sorry
tricky
'''
        output = autograder.run_submission(start_folder, args, input)
    except Exception as e:
        return autograder.make_submission_error_page(str(e), session)
    if output.find('debug mode') < 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('When I passed in the "debug" flag, it did not print that it was running in debug mode. (See step 2.j)')
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }
    if output.find('delta') < 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('The words in the lexicon were not displayed when in debug mode.')        
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }
    if output.find('rascal') >= 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('I was able to enter more than 8 words into the lexicon. (See step 5.a)')        
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }

    # Test 3: superfluous argument
    try:
        args = ['debug', 'salmon']
        input = '''alpha
beta
charlie
delta
epsilon
frank
george
harry
indigo
jackson
kappa
llama
money
nubile
oscar
petrify
quirky
rascal
sorry
tricky
'''
        output = autograder.run_submission(start_folder, args, input)
    except Exception as e:
        return autograder.make_submission_error_page(str(e), session)
    if output.find('delta') >= 0:
        p.append('<font color="red">Sorry, there was an issue.</font><br><br>')
        p.append('When I passed in a superfluous argument, it did not crash. (See step 2.j)')
        autograder.page_end(p)
        return {
            'content': ''.join(p),
        }

    # Accept the submission
    covered_days = min(days_late, account["toks"])
    account["toks"] -= covered_days
    days_late -= covered_days
    score = max(30, 100 - 3 * days_late)
    log(f'Passed: title={title_clean}, student={session.name}, days_late={days_late}, score={score}')
    account[title_clean] = score
    autograder.save_accounts(course_desc['accounts'], accounts)
    p.append('<font color="green">Your submission passed all tests! Your assignment is complete. You have tentatively been given full credit.')
    p.append('(However, the grade is not final until the grader looks at it.)</font>')
    autograder.page_end(p)
    return {
        'content': ''.join(p),
    }



def pf2_proj1_submit(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_submission_page(
        params,
        session,
        course_desc['course'],
        course_desc['projects']['proj1'],
        accounts,
        course_desc['accounts'],
        'pf2_proj1_submit.html',
        'pf2_proj1_receive.html',
    )

def pf2_proj2_submit(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_submission_page(
        params,
        session,
        course_desc['course'],
        course_desc['projects']['proj2'],
        accounts,
        course_desc['accounts'],
        'pf2_proj2_submit.html',
        'pf2_proj2_receive.html',
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
    student_list = '''
Adair,Britton Brosh
Adair,Katelynn Mae
Aguirre Herrera,Emil Josue
Aldana,Bryan D
Alserhan,Shdan Mohammad Sul
Anderson II,Will Turner
Andrade,Dmetri Arnaldo
Arigbede,Adedayo J
Bailey,Zack Kyle
Baranczuk,Ethan C
Bean,Tyler James Richard
Bentley,Faith E
Blake,Kobe Jamal
Bodishbaugh,Jake A
Braddy,Hunter W
Bullard,Harrison Jeffrey
Calhoun,Nicholas R
Cassels,Lauren
Castaneda,Alan
Chance,Evan K
Childers,Cade G
Clelland,Timothy J
Coffman,Ethan J
Cooper,Cole
Corona,Juju
Craddock,Matthew James
Crosby,Chloe L
Davis,Ashton Brian
Debose Laughton,Lucas M
Delgado,Alain A
Devaney,Brian Patrick
Dodia,Dhairya Ritesh
Dou,Madison R
Dunn,Bradley J
Elashwah,Nada
Elliott,Cameron B
Evans,Brigham Kennedy
Ewing,Timothy Shane
Eyres,Ian P
Favela-Romo,Tania
Fitzgerl,William Edward
Florini,Joseph J
Gashler,Mike
Golson,Conor Nolan
Gordin,Daniel Alexander
Graham,Jackson Foster
Green,Ethan
Green,Matthew Clark
Guin,Joshua
Gunderman,Benjamin Owen
Guo,Jay
Gutierrez,Rover Juliann Belisario
Hamilton,Jayden Greggory
Hernandez,Diana
Herring,Nicholas Wade
Hinkle,Tate B
Hoang,Amy
Hogue,Lucas Timothy
Holland,Gavin Alexander
Hughes,Jacob Ryan
Iqbal,Faria
Jachim,Nicholas Jeffrey
Johnson,Garrett David
Jones,Kyler
Kavi,Alekhya
Kay,Dantea
Keck,Caroline Elise
Kessler,Zachary P
Key,Brandon L
Khan,Ahmed
Khan,Ali Mohammad
Koonce,Shane C
Landivar Scott,Leonardo
Lee,A'Darius Jamal
Lemon,McKayla Jana
Long,Jason Michael
Luceri IV,Frank Anthony
Lucero,Kevin D
Lwando,Alex Mwelwa
Mahan,Hayden C
Mallapally,Varun R
Martinez,Madison Miranda
McCollum,Micah Lee
McDougall,Ethan A
McMullen,Isaac Hudson
Montano,Adam Ethan
Morgan,Brady A
Morris,Lillian Mikayla
Murphy,Daniel Joseph
Name
Navarro,Amanda Rose Perez
Nguyen,Minh Duy
Nieves,Eduardo
Ninh,Khang D
Norden,Shane Keith
Northington,Peyton E
Palencia,Elmer
Panda,Nandita
Pham,Tyler H
Phifer,Colin Thomas
Phillips,Isaac Michael
Pinkerton,Jacob Ryan
Proctor,Timothy Cole
Pumford,Milo
Pyburn,William James
Quach,Katelyn T
Ramsey,Landon Scott
Raper,Jacob H
Reeves,Trevor Dean
Rhame,Marlan L
Richardson,Elizabeth Grace
Ridgeway,Mary-Claire Mayuga
Rivas,Daniel Omar
Roberts,Warren Lee
Robertson,Logan P
Rocha,Jonathan A
Rodriguez,Aaron
Rodriguez,Daniel Tomas
Rogers,Cody P
Rose,Eli J
Saenz,Brian
Salazar,Adrian Christofer
Sanchez,Tony
Sandoval,Christian A
Schlageter,Dylan Hufton
Schroeder,Tyler James
Serna-Aguilera,Manuel
Shanti,Raheem Bassam
Shufelt III,James Peter
Smith,Dalton D
Smith,Nicholas Henry
Smith,Sarah Mei
Stelting,Brennan C
Stroud,Dylan T
Stuart,Renee M
Suresh Babu,Siddarth
Thompson,Gabriel Bishop
Trudo,Todd A
Trujillo,Marco
Van Norman IV,Russell Howard
Vangoor,Santosh R
Verma,Akshath Akhilesh
Villalobos,Christian A
Wade,Randalll G
Watson,Carter J
White,Phoebe Katherine
Wilkins,Dylan Jay
Wilkins,Eric Fritsch
Wilkinson,Matthew M
Williams,Bryan C
Williams,Draper Bernard
Wilson,Adam J
Wilson,Nathaniel L
Wise,Jacob M
Young,Caleb S
Young,Eli
Zheng,Hu
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
