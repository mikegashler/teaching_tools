from typing import Mapping, Any, List, Dict, cast
from datetime import datetime
from http_daemon import Session, log
from datetime import datetime
from threading import Lock
import autograder
import sys
import re

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

def basic_checks(args:List[str], input:str, output:str) -> None:
    if output.find('error:') >= 0:
        raise autograder.RejectSubmission(
            'It looks like there were errors.',
            args, input, output,
        )
    if output.find('segmentation fault') >= 0:
        raise autograder.RejectSubmission(
            'It looks like there was a segmentation fault. (This means you wrote to some place in memory you did not allocate.)',
            args, input, output,
        )

def evaluate_proj1(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it produces the exactly correct output

    args = ['aaa', 'bbb', 'ccc']
    input = '''Aloysius
8'''
    output = autograder.run_submission(submission, args, input)
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
    if output != expected:
        raise autograder.RejectSubmission(
            'The output does not match the expected output.',
            args, input, output,
            f'Expected output: <pre class="code">{expected}</pre><br><br>',
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj2(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: not debug mode, exactly 8 items
    args:List[str] = []
    input = '''alpha
beta
charlie
delta
epsilon
flag
gum
hair
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('debug mode') >= 0:
        raise autograder.RejectSubmission(
            'I did not pass in the "debug" flag, but it still ran in debug mode!',
            args, input, output,
        )
    if output.find('delta') < 0:
        raise autograder.RejectSubmission(
            'The words in the lexicon were not displayed when not in debug mode.',
            args, input, output,
        )

    # Test 2: debug mode, long list
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
    if output.find('debug mode') < 0:
        raise autograder.RejectSubmission(
            'When I passed in the "debug" flag, it did not print that it was running in debug mode. (See step 2.j)',
            args, input, output,
        )
    if output.find('delta') < 0:
        raise autograder.RejectSubmission(
            'The words in the lexicon were not displayed when in debug mode.',
            args, input, output,
        )
    if output.find('rascal') >= 0:
        raise autograder.RejectSubmission(
            'I was able to enter more than 8 words into the lexicon. (See step 5.a)',
            args, input, output,
        )

    # Test 3: superfluous argument
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
    if output.find('delta') >= 0:
        raise autograder.RejectSubmission(
            'When I passed in a superfluous argument, it did not crash. (See step 2.j)',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj3(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: Make sure the name was changed and it prints words entered so far
    args:List[str] = []
    input = '''1
alpha
beta
gamma

0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('Aloysius') >= 0:
        raise autograder.RejectSubmission(
            'You were supposed to change the name. See step 2.b.',
            args, input, output,
        )
    if output.find('beta') < 0:
        raise autograder.RejectSubmission(
            'When the "quiet" flag is not used, you are supposed to print the words that have been entered so far.',
            args, input, output,
        )

    # Test 2: Make sure the quiet flag works
    args = ['quiet']
    input = '''1
alpha
beta
gamma

0
'''
    output = autograder.run_submission(submission, args, input)
    if output.find('beta') >= 0:
        raise autograder.RejectSubmission(
            'When the "quiet" flag is used, you are not supposed to print the words that have been entered so far.',
            args, input, output,
        )

    # Test 3: Make sure it can handle a lot of words and the tear-down works
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

2
0
'''
    output = autograder.run_submission(submission, args, input)
    narwhal_spot = output.rfind('narwhal')
    elephant_spot = output.rfind('elephant')
    if narwhal_spot < 0 or elephant_spot < 0:
        raise autograder.RejectSubmission(
            'Expected the tear-down to print the lexicon in reverse order. But at least some of the animals I pushed on the stack were not printed!',
            args, input, output,
        )
    if elephant_spot < narwhal_spot:
        raise autograder.RejectSubmission(
            'The list was not correctly reversed.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj4(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it produces the exactly correct output
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
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('#///#   #') < 0:
        raise autograder.RejectSubmission(
            'Flood fill did not work correctly. It should have filled the left-side box with slashes, but left the right-side box empty.',
            args, input, output,
        )

    # Test 1: See if it produces the exactly correct output
    args = ['quiet']
    input = '''3
###### ######
#   #   #   #
#       #   #
#   #   #
## ##########

5
2
2
x
100
4
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('#xxx#xxx#   #') < 0:
        raise autograder.RejectSubmission(
            'Flood fill did not work correctly. It should have filled the left two regions with "x"s, but left the right-most region empty.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj5(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: Test Boggle output
    args = ['quiet']
    input = '''3
ijkl
mnop
qrst
uvwx

1
aaaaaaaa
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
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('aaaaaaaa') >= 0:
        raise autograder.RejectSubmission(
            f'When the "quiet" flag is used, you are not supposed to print all the words in your lexicon.',
            args, input, output,
        )
    for word in ['in', 'ink', 'inkpots', 'inro', 'jink',
                 'knops', 'knots', 'lost', 'minors',
                 'plonk', 'storm', 'urns']:
        if output.find(word) < 0:
            raise autograder.RejectSubmission(
                f'Failed to find the word "{word}".',
                args, input, output,
            )
    for word in ['poop', 'tot']:
        if output.find(word) >= 0:
            raise autograder.RejectSubmission(
                f'It looks like your implementation does not prevent letters from being used multiple times. For example, your implementation reported the invalid word "{word}".',
                args, input, output,
            )
    for word in ['salad', 'salmon', 'taco', 'wrist', 'six']:
        if output.find(word) >= 0:
            raise autograder.RejectSubmission(
                f'Found the invalid word "{word}". (Make sure you are not printing all the words in your lexicon. That will cause the autograder to think you are finding them in the CharMatrix.)',
                args, input, output,
            )
    if output.find('porn') >= 0:
        raise autograder.RejectSubmission(
            f'Found the word "porn", which was not even in the lexicon!',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj6(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if the unit test passes
    args = ['quiet']
    input = '''7
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('passed') < 0 and output.find('Passed') < 0:
        raise autograder.RejectSubmission(
            'The unit test did not pass. (Did not find the string "passed" in the output.)',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj7(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: Sort a very small list
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
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    words_in_order = ['zebra', 'monkey', 'alligator', 'pizza', 'cheese', 'salad']
    prev = -1
    for i in range(len(words_in_order)):
        pos = output.rfind(words_in_order[i])
        if pos < 0:
            raise autograder.RejectSubmission(
                f'Expected to find the word {words_in_order[i]} in the output.',
                args, input, output,
            )
        elif pos <= prev:
            raise autograder.RejectSubmission(
                f'The sorted order was wrong. {words_in_order[i]} should have come after {words_in_order[i - 1]}.',
                args, input, output,
            )
        prev = pos
    comp = 'comparisons:'    
    comp_pos = output.find(comp)
    if comp_pos < 0:
        raise autograder.RejectSubmission(
            f'Did not find the string "comparisons: " in your output. See step 2.d.',
            args, input, output,
        )
    comp_pos += len(comp)
    try:
        comp_val = next_num(output[comp_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            f'Expected a number after "{comp}"',
            args, input, output,
        )
    if comp_val <= 6 or comp_val >= 16:
        raise autograder.RejectSubmission(
            f'The number of comparisons performed ({comp_val}) is not consistent with mergesort. Are you counting comparisons correctly?',
            args, input, output,
        )

    # Test 2: Sort a bigger list
    args = ['quiet']
    input = '1\n' + ('xyz\n' * 1024) + '\n8\n0\n'
    output = autograder.run_submission(submission, args, input)
    comp = 'comparisons:'
    comp_pos = output.find(comp)
    if comp_pos < 0:
        raise autograder.RejectSubmission(
            f'Did not find the string "comparisons: " in your output. See step 2.d.',
            args, input, output,
        )
    try:
        comp_val = next_num(output[comp_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            f'Expected a number after {comp}',
            args, input, output,
        )
    if comp_val <= 5118 or comp_val >= 10241:
        raise autograder.RejectSubmission(
            f'The number of comparisons performed is not consistent with mergesort. Are you counting comparisons correctly?',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj8(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it produces the exactly correct output
    args = ['quiet']
    input = '''9
/var/www/autograder/test_data/db.csv
10
0
dog
fish
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
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
            'Expected the doughnut row to come before the eggs row',
        args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )

    # Test 1: See if it produces the exactly correct output
    args = ['quiet']
    input = '''9
/var/www/autograder/test_data/db.csv
10
2
0
4
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    eggs_pos = output.find('eggs')
    if eggs_pos >= 0:
        raise autograder.RejectSubmission(
            'Did not expect the eggs row to be in the output.',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
    eggs_pos = output.find('doughnut')
    if eggs_pos >= 0:
        raise autograder.RejectSubmission(
            'Did not expect the doughnut row to be in the output. Did you use smart_compare for all comparisons?',
            args, input, output, autograder.display_data('/var/www/autograder/test_data/simple.csv')
        )
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

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj9(submission:Mapping[str,Any]) -> Mapping[str, Any]:

    # Test 1: Measure baseline values for the number of instantiations and deletions
    args = ['quiet']
    input = '''11
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)    
    inst_pos = output.find('instantiated:')
    if inst_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the string "instantiated:" to occur in the output',
            args, input, output,
        )
    try:
        baseline_inst_val = next_num(output[inst_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            'Expected a number after "instantiated:"',
            args, input, output,
        )
    dele_pos = output.find('deleted:')
    if dele_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the string "deleted:" to occur in the output',
            args, input, output,
        )
    try:
        baseline_dele_val = next_num(output[dele_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            'Expected a number after "deleted:"',
            args, input, output,
        )
    if baseline_inst_val >= 7:
        raise autograder.RejectSubmission(
            'I did not even do anything. How many global objects do you have?',
            args, input, output,
        )
    if baseline_dele_val > baseline_inst_val:
        raise autograder.RejectSubmission(
            'How do you have more deletions than instantiations?',
            args, input, output,
        )

    # Test 2: See if the gap is the same
    args = ['quiet']
    input = '''1
apple
1 zither
cheese
22 xylophone
banana
3 didgeridoo

3
appl
ehse
cesb
anaa

4
6
7
8
9
/var/www/autograder/test_data/db.csv
10
2
0
4
11
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)    
    inst_pos = output.find('instantiated:')
    if inst_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the string "instantiated:" to occur in the output',
            args, input, output,
        )
    try:
        inst_val = next_num(output[inst_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            'Expected a number after "instantiated:"',
            args, input, output,
        )
    dele_pos = output.find('deleted:')
    if dele_pos < 0:
        raise autograder.RejectSubmission(
            'Expected the string "deleted:" to occur in the output',
            args, input, output,
        )
    try:
        dele_val = next_num(output[dele_pos:])
    except ValueError:
        raise autograder.RejectSubmission(
            'Expected a number after "deleted:"',
            args, input, output,
        )
    if inst_val < 7:
        raise autograder.RejectSubmission(
            'The total number of instantiations is too small. It looks like you are not counting instantiations properly.',
            args, input, output,
        )
    if dele_val > inst_val:
        raise autograder.RejectSubmission(
            'The total number of deletions should not be larger than the number of instantiations. (This often means you are passing objects by value that lack a copy constructor.)',
            args, input, output,
        )

    if inst_val - dele_val != baseline_inst_val - baseline_dele_val:
        raise autograder.RejectSubmission(
            'The gap between instantiations and deletions changed when more code was run. This suggests you probably have memory leaks that are not just due to global variables.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj10(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it produces the exactly correct output
    args = ['quiet']
    input = '''12
taco
acotay
12
rice
iceray
12
pineapple
ineapplepay
13
taco
13
pineapple
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    if output.find('iceray') >= 0:
        raise autograder.RejectSubmission(
            'Did not expect to find "iceray" in the output. I did not query for "rice"!',
            args, input, output,
        )
    if output.find('ineapplepay') < 0:
        raise autograder.RejectSubmission(
            'Expected to find "ineapplepay" in the output.',
            args, input, output,
        )
    if output.find('acotay') < 0:
        raise autograder.RejectSubmission(
            'Expected to find "acotay" in the output.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_proj11(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    # Test 1: See if it produces the exactly correct output
    args = ['quiet']
    input = '''14
salmon
14
money
14
tarantula
14
banana
14
zebra
14
antelope
15
15
15
15
15
15
0
'''
    output = autograder.run_submission(submission, args, input)
    basic_checks(args, input, output)
    words_in_order = ['antelope', 'banana', 'money', 'salmon', 'tarantula', 'zebra']
    prev = -1
    for i in range(len(words_in_order)):
        pos = output.rfind(words_in_order[i])
        if pos < 0:
            raise autograder.RejectSubmission(
                f'Expected to find the word {words_in_order[i]} in the output.',
                args, input, output,
            )
        elif pos <= prev:
            raise autograder.RejectSubmission(
                f'The order was wrong. {words_in_order[i]} should have come after {words_in_order[i - 1]}.',
                args, input, output,
            )
        prev = pos

    # Accept the submission
    return accept_submission(submission)

course_desc:Mapping[str,Any] = {
    'course_long': 'Programming Foundations II',
    'course_short': 'pf2',
    'accounts': 'pf2_accounts.json',
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
            'due_time': datetime(year=2024, month=2, day=12, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj3,
        },
        'proj4': {
            'title': 'Project 4',
            'due_time': datetime(year=2024, month=2, day=19, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj4,
        },
        'midterm1': {
            'title': 'Midterm 1',
            'due_time': datetime(year=2024, month=2, day=26, hour=23, minute=59, second=59),
            'weight': 18,
            'points': 86,
        },
        'proj5': {
            'title': 'Project 5',
            'due_time': datetime(year=2024, month=3, day=4, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj5,
        },
        'proj6': {
            'title': 'Project 6',
            'due_time': datetime(year=2024, month=3, day=11, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj6,
        },
        'proj7': {
            'title': 'Project 7',
            'due_time': datetime(year=2024, month=3, day=25, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj7,
        },
        'midterm2': {
            'title': 'Midterm 2',
            'due_time': datetime(year=2024, month=4, day=1, hour=23, minute=59, second=59),
            'weight': 18,
            'points': 67,
        },
        'proj8': {
            'title': 'Project 8',
            'due_time': datetime(year=2024, month=4, day=15, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj8,
        },
        'proj9': {
            'title': 'Project 9',
            'due_time': datetime(year=2024, month=4, day=22, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj9,
        },
        'proj11': {
            'title': 'Project 11',
            'due_time': datetime(year=2024, month=4, day=29, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 4,
            'evaluator': evaluate_proj11,
        },
        'lab': {
            'title': 'Lab participation',
            'due_time': datetime(year=2024, month=5, day=2, hour=23, minute=59, second=59),
            'weight': 4,
            'points': 4,
        },
        'final': {
            'title': 'Final exam',
            'due_time': datetime(year=2024, month=5, day=8, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 100,
        },
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
except:
    print('*** FAILED TO LOAD PF2 ACCOUNTS! Starting an empty file!!!')
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
    return autograder.view_scores_page(params, session, 'pf2_view_scores.html', accounts, course_desc)

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
    try:
        accounts:Dict[str,Any] = autograder.load_accounts(course_desc['accounts'])
    except:
        accounts = {}
    autograder.save_accounts(course_desc['accounts'], accounts)

if __name__ == "__main__":
    initialize_accounts()
