from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
import autograder

def evaluate_proj1(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj1', accounts, 'pf2_proj1_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['aaa', 'bbb', 'ccc']
        input = '''Aloysius
8'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
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
        return autograder.reject_submission(session,
            'The output does not match the expected output.',
            args, input, output,
            f'Expected output: <pre class="code">{expected}</pre><br><br>',
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj2(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj2', accounts, 'pf2_proj2_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: not debug mode, short list
    try:
        args:List[str] = []
        input = '''alpha
beta
charlie
delta
epsilon
'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('debug mode') >= 0:
        return autograder.reject_submission(session,
            'I did not pass in the "debug" flag, but it still ran in debug mode!',
            args, input, output,
        )
    if output.find('delta') < 0:
        return autograder.reject_submission(session,
            'The words in the lexicon were not displayed when not in debug mode.',
            args, input, output,
        )

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
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('debug mode') < 0:
        return autograder.reject_submission(session,
            'When I passed in the "debug" flag, it did not print that it was running in debug mode. (See step 2.j)',
            args, input, output,
        )
    if output.find('delta') < 0:
        return autograder.reject_submission(session,
            'The words in the lexicon were not displayed when in debug mode.',
            args, input, output,
        )
    if output.find('rascal') >= 0:
        return autograder.reject_submission(session,
            'I was able to enter more than 8 words into the lexicon. (See step 5.a)',
            args, input, output,
        )

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
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('delta') >= 0:
        return autograder.reject_submission(session,
            'When I passed in a superfluous argument, it did not crash. (See step 2.j)',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj3(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj3', accounts, 'pf2_proj3_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: Make sure the name was changed and it prints words entered so far
    try:
        args:List[str] = []
        input = '''1
alpha
beta
gamma'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('Aloysius') >= 0:
        return autograder.reject_submission(session,
            'You were supposed to change the name. See step 2.b.',
            args, input, output,
        )
    if output.find('beta') < 0:
        return autograder.reject_submission(session,
            'When the "quiet" flag is not used, you are supposed to print the words that have been entered so far.',
            args, input, output,
        )

    # Test 2: Make sure the quiet flag works
    try:
        args = ['quiet']
        input = '''1
alpha
beta
gamma'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('beta') >= 0:
        return autograder.reject_submission(session,
            'When the "quiet" flag is used, you are not supposed to print the words that have been entered so far.',
            args, input, output,
        )

    # Test 3: Make sure it can handle a lot of words and the tear-down works
    try:
        args = ['quiet']
        input = '''1
alligator
babboon
cat
dog
elephant
frog
giraffe
human
iguana
jackal
kangaroo
llama
monkey
narwhal
ostrich
pig
'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    narwhal_spot = output.find('narwhal')
    elephant_spot = output.find('elephant')
    if narwhal_spot < 0 or elephant_spot < 0:
        return autograder.reject_submission(session,
            'Some of the animals I pushed on the stack disappeared!',
            args, input, output,
        )
    if elephant_spot < narwhal_spot:
        return autograder.reject_submission(session,
            'The list was not correctly reversed.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj4(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj4', accounts, 'pf2_proj4_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''3
#########
#   #   #
#   #   #
#   #   #
#########

5
2
2
/
100

4

'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('#///#   #') < 0:
        return autograder.reject_submission(session,
            'Flood fill did not work correctly. It should have filled the left-side box with slashes, but left the right-side box empty.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj5(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj5', accounts, 'pf2_proj5_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''3
ijkl
mnop
qrst
uvwx

1
in
ink
inkpot
inkpots
inro
ins
jin
jink
jins
jo
jot
jots
knop
knops
knosp
knot
knots
kop
kops
kor
kors
kos
lo
lop
lops
lorn
lost
lot
lots
mi
mink
minor
minors
nim
no
nor
norm
nos
not
on
ons
op
ops
opt
opts
or
ors
os
plonk
plot
plots
pol
pons
poop
post
pot
pots
rot
rots
salad
salmon
six
snot
so
sol
son
sop
sorn
sot
spot
stop
storm
taco
to
ton
tons
top
tops
tor
torn
tors
tot
urn
urns
wrist

6
'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    for word in ['in', 'ink', 'inkpots', 'inro', 'jink',
                 'knops', 'knots', 'lost', 'minors',
                 'plonk', 'storm', 'urns']:
        if output.find(word) < 0:
            return autograder.reject_submission(session,
                f'Failed to find the word "{word}".',
                args, input, output,
            )
    for word in ['poop', 'tot']:
        if output.find(word) >= 0:
            return autograder.reject_submission(session,
                f'It looks like your implementation does not prevent letters from being used multiple times. For example, your implementation reported the invalid word "{word}".',
                args, input, output,
            )
    for word in ['salad', 'salmon', 'taco', 'wrist', 'six']:
        if output.find(word) >= 0:
            return autograder.reject_submission(session,
                f'Found the invalid word "{word}".',
                args, input, output,
            )
    if output.find('porn') >= 0:
        return autograder.reject_submission(session,
            f'Found the word "porn", which was not even in the lexicon!',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj6(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj6', accounts, 'pf2_proj6_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''7
'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('passed') < 0:
        return autograder.reject_submission(session,
            'The unit test did not pass.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj7(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj7', accounts, 'pf2_proj7_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: Sort a very small list
    try:
        args = ['quiet']
        input = '''1
monkey
1 salad
alligator
11 pizza
zebra
8 cheese

8
2
'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    words_in_order = ['zebra', 'monkey', 'alligator', 'pizza', 'cheese', 'salad']
    prev = -1
    for i in range(len(words_in_order)):
        pos = output.find(words_in_order[i])
        if i > 0 and pos <= prev:
            return autograder.reject_submission(session,
                f'The sorted order was wrong. {words_in_order[i]} should have come after {words_in_order[i - 1]}.',
                args, input, output,
            )
        prev = pos
    comp = 'comparisons: '
    comp_pos = output.find(comp)
    if comp_pos < 0:
        return autograder.reject_submission(session,
            f'Did not find the string "comparisons: " in your output. See step 2.d.',
            args, input, output,
        )
    comp_pos += len(comp)
    i = 0
    while output[comp_pos + i].isdigit():
        i += 1
    if i == 0:
        return autograder.reject_submission(session,
            f'Expected a number after "comparisons: ". See step 2.d.',
            args, input, output,
        )
    comp_val = int(output[comp_pos:comp_pos + 1])
    if comp_val <= 6 or comp_val >= 16:
        return autograder.reject_submission(session,
            f'The number of comparisons performed is not consistent with mergesort. Are you counting comparisons correctly?',
            args, input, output,
        )

    # Test 2: Sort a bigger list
    try:
        args = ['quiet']
        input = '1\n' + ('xyz' * 1024) + '\n8\n'
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    comp = 'comparisons: '
    comp_pos = output.find(comp)
    if comp_pos < 0:
        return autograder.reject_submission(session,
            f'Did not find the string "comparisons: " in your output. See step 2.d.',
            args, input, output,
        )
    comp_pos += len(comp)
    i = 0
    while output[comp_pos + i].isdigit():
        i += 1
    if i == 0:
        return autograder.reject_submission(session,
            f'Expected a number after "comparisons: ". See step 2.d.',
            args, input, output,
        )
    comp_val = int(output[comp_pos:comp_pos + 1])
    if comp_val <= 5118 or comp_val >= 10241:
        return autograder.reject_submission(session,
            f'The number of comparisons performed is not consistent with mergesort. Are you counting comparisons correctly?',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj8(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj8', accounts, 'pf2_proj8_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''Aloysius
8'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Did not find xxx.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj9(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj9', accounts, 'pf2_proj9_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''Aloysius
8'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Did not find xxx.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj10(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj10', accounts, 'pf2_proj10_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''Aloysius
8'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Did not find xxx.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

def evaluate_proj11(params:Mapping[str, Any], session:Session) -> Mapping[str, Any]:
    # Unpack the submission
    submission = autograder.unpack_submission(params, session, course_desc, 'proj11', accounts, 'pf2_proj11_submit.html')
    if not 'succeeded' in submission or not submission['succeeded']:
        return cast(Mapping[str,Any], submission['page'])

    # Test 1: See if it produces the exactly correct output
    try:
        args = ['quiet']
        input = '''Aloysius
8'''
        output = autograder.run_submission(submission, args, input)
    except Exception as e:
        return autograder.reject_submission(session, str(e))
    if output.find('error:') >= 0:
        return autograder.reject_submission(session,
            'It looks like there were compile errors.',
            args, input, output,
        )
    if output.find('xxx') < 0:
        return autograder.reject_submission(session,
            'Did not find xxx.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(session, submission)

course_desc:Mapping[str,Any] = {
    'course_long': 'Programming Foundations II',
    'course_short': 'pf2',
    'accounts': 'pf2_accounts.json',
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
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD PF2 ACCOUNTS! Starting an empty file!!!')
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
    return autograder.make_admin_page(params, session, 'pf2_admin.html', accounts, course_desc)

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
