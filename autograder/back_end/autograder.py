from typing import Mapping, Any, List, Dict, cast, Callable, Optional, Tuple
import json
import shutil
import zipfile
import os
from datetime import datetime, timedelta
from http_daemon import Session, log
import traceback
import threading
import random
import string

os.chdir(os.path.join(os.path.dirname(__file__), '../front_end'))

change_me_hash = "ff854dee05ef262a4219cddcdfaff1f149203fd17d6f4db8454bf5f3d75470c3a4d0ee421257a27a5cb76358167fe6d4562d2e25c10ae7ad9c14492178df5551"

def load_accounts(filename:str) -> Dict[str,Any]:
    with open(filename, 'r') as f:
        accounts = f.read()
    return cast(Dict[str,Any], json.loads(accounts))

def save_accounts(filename:str, accounts:Dict[str,Any]) -> None:
    with open(filename, 'w') as f:
        f.write(json.dumps(accounts, indent=2))

def add_students(names:List[str], accounts:Dict[str,Any], toks:int=7) -> None:
    for name in names:
        if len(name) == 0:
            continue
        accounts[name] = {
            'pw': change_me_hash,
            'toks': toks,
        }

launch_script_with_sandbox = '''#!/bin/bash
set -e

# Make sure the files are owned by sandbox
sudo chown sandbox:sandbox .
sudo chown -R sandbox:sandbox *

# Make sure the script has unix line endings, and is executable
sudo dos2unix -q ./run.bash
sudo chmod 755 ./run.bash

# Launch the "run.bash" script
sudo -u sandbox ./run.bash $* < _stdin.txt &

# Start a time-out timer
CHILD_PID=$!
TIME_LIMIT=30
for (( i = 0; i < $TIME_LIMIT; i++ )); do
	sleep 1

	#proc=$(ps -ef | awk -v pid=$CHILD_PID '$2==pid{print}{}')
	#if [[ -z "$proc" ]]; then
	#	break
	#fi

	if ! ps -p $CHILD_PID > /dev/null; then
		break
	fi
done
if [ $i -lt $TIME_LIMIT ]; then
	echo ""
else
	echo "!!! Time limit exceeded! Killing the unfinished process !!!"
	sudo kill -HUP $CHILD_PID
    sleep 1
    sudo kill -15 $CHILD_PID
    sleep 1
	sudo kill -9 $CHILD_PID
fi

# Clean up some generated files
cd ..
if [ -d "obj" ]; then
	find . -name "*.class"  -exec -exec rm {} \;
	find . -name "*.o"  -exec -exec rm {} \;
	find . -name "*.obj"  -exec -exec rm {} \;
	find . -name "*.ncb"  -exec -exec rm {} \;
	find . -name "*.suo"  -exec -exec rm {} \;
	find . -name "*.pch"  -exec -exec rm {} \;
	find . -name "*.lib"  -exec -exec rm {} \;
	find . -name "*.a"  -exec -exec rm {} \;
fi
'''

launch_script_without_sandbox = '''#!/bin/bash
set -e

# Make sure the script has unix line endings, and is executable
dos2unix -q ./run.bash
chmod 755 ./run.bash

# Launch the "run.bash" script
./run.bash $* < _stdin.txt &

# Start a time-out timer
CHILD_PID=$!
TIME_LIMIT=30
for (( i = 0; i < $TIME_LIMIT; i++ )); do
	sleep 1

	#proc=$(ps -ef | awk -v pid=$CHILD_PID '$2==pid{print}{}')
	#if [[ -z "$proc" ]]; then
	#	break
	#fi

	if ! ps -p $CHILD_PID > /dev/null; then
		break
	fi
done
if [ $i -lt $TIME_LIMIT ]; then
	echo ""
else
	echo "!!! Time limit exceeded! Killing the unfinished process !!!"
	sudo kill -HUP $CHILD_PID
    sleep 1
    sudo kill -15 $CHILD_PID
    sleep 1
	sudo kill -9 $CHILD_PID
fi

# Clean up some generated files
cd ..
if [ -d "obj" ]; then
	find . -name "*.class"  -exec -exec rm {} \;
	find . -name "*.o"  -exec -exec rm {} \;
	find . -name "*.obj"  -exec -exec rm {} \;
	find . -name "*.ncb"  -exec -exec rm {} \;
	find . -name "*.suo"  -exec -exec rm {} \;
	find . -name "*.pch"  -exec -exec rm {} \;
	find . -name "*.lib"  -exec -exec rm {} \;
	find . -name "*.a"  -exec -exec rm {} \;
fi
'''

# Executes a submission with the specified args and input, and returns its output
def run_submission(submission:Mapping[str,Any], args:List[str]=[], input:str='', sandbox:bool=True) -> str:
    # Write the input to a file
    start_folder = submission['folder']
    with open(os.path.join(start_folder, '_stdin.txt'), 'w') as f:
        f.write(input)
        f.write('\n\n\n\n\n\n\n\n') # Add a few newlines to flush any superfluous input prompts

    # Put a launch script in the same folder as run.bash
    with open(os.path.join(start_folder, '_launch.bash'), 'w') as f:
        f.write(launch_script_with_sandbox if sandbox else launch_script_without_sandbox)

    # Execute the launch script
    os.system(f'cd {start_folder}; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)} > _stdout.txt 2> _stderr.txt')

    # Read the output
    with open(os.path.join(start_folder, '_stdout.txt'), 'r') as f:
        stdout = f.read()
    with open(os.path.join(start_folder, '_stderr.txt'), 'r') as f:
        stderr = f.read()
    return stdout + stderr

# Receives a submission. Unzips it. Checks for common problems.
# Executes it, and returns the output as a string.
# Throws a ValueError if anything is wrong with the submission.
def receive_and_unpack_submission(params:Mapping[str, Any], course:str, project:str, student:str) -> str:
    # Make sure we received a zip file
    zipfilename = params['filename']
    _, extension = os.path.splitext(zipfilename)
    if not extension == '.zip':
        raise ValueError(f'Expected a file with the extension ".zip". Got "{extension}".')

    # Make a folder for the submission
    t = datetime.now()
    date_stamp = f'{t.year:04}-{t.month:02}-{t.day:02}_{t.hour:02}-{t.minute:02}-{t.second:02}-{t.microsecond:06}'
    student = student.replace(' ', '_').replace(',', '_').replace('\'', '_')
    basename = os.path.join(course, project, student, date_stamp)
    log(f'making dirs: {basename}')
    os.makedirs(basename)
    zipname = os.path.join(basename, os.path.basename(zipfilename))

    # Unzip it
    log(f'moving {zipfilename} to {zipname}')
    shutil.move(zipfilename, zipname)
    with zipfile.ZipFile(zipname, 'r') as zip_ref:
        zip_ref.extractall(basename)

    # Check for forbidden files or folders, and find the run.bash script
    forbidden_folders = [
        '.DS_Store', 
        '.mypy_cache', 
        '__pycache__', 
        '.git', 
        '__MACOSX', 
        '.settings',
        'backup',
        'data',
        'images',
        'pics',
    ]
    forbidden_extensions = [
        '', # usually compiled C++ apps
        '.arff',
        '.bat', # windows batch files
        '.class', # compiled java
        '.csv',
        '.dat',
        '.exe', 
        '.htm',
        '.html',
        '.json',
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
        '.txt',
    ]
    file_count = 0
    start_folder = ''
    for path, folders, files in os.walk(basename):
        for forbidden_folder in forbidden_folders:
            if forbidden_folder in folders:
                raise ValueError(f'Your zip file contains a forbidden folder: "{forbidden_folder}".')
        for filename in files:
            _, ext = os.path.splitext(filename)
            for forbidden_extension in forbidden_extensions:
                if ext == forbidden_extension:
                    raise ValueError(f'Your zip contains an unnecessary file: "{filename}". Please submit only your code and build script.')
        file_count += len(files)
        if 'run.bash' in files:
            start_folder = path

    # Check that there are not too many files
    max_files = 50
    if file_count > max_files:
        raise ValueError(f'Your zip file contains {file_count} files! Only {max_files} are allowed.')

    # Check that a 'run.bash' file was found somewhere in the archive
    if start_folder == '':
        raise ValueError(f'No "run.bash" file was found in your submission.')
    return start_folder

# This is the header at the top of every page
def page_start(p:List[str], session:Session) -> None:
    p.append('<!DOCTYPE html>')
    p.append('<html><head>')
    p.append('<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">')
    p.append('<style>')
    p.append('body,center {')
    p.append('  font-family: verdana, tahoma, geneva, sans-serif;')
    p.append('  font-size: 24px;')
    p.append('  background-color:#cacaca;')
    p.append('}')
    p.append('.code {')
    p.append('  color:#a0ffa0;')
    p.append('  background-color:#000000;')
    p.append('  width:100%;')
    p.append('  overflow-x:scroll;')
    p.append('}')
    p.append('</style>')
    p.append('<script src="sha512.js"></script>')
    p.append('</head>')
    p.append('<body><table width="800px" align="center" style="background: #ffffff;"><tr><td>')
    p.append('<img src="banner.png"><br>')
    if session.logged_in():
        p.append(f'Logged in as <b>{session.name}</b>. <a href="log_out.html">Log out</a>')
    else:
        p.append('(Not currently logged in)')
    p.append('<br><br>')

# This is the footer at the bottom of every page
def page_end(p:List[str]) -> None:
    p.append('<br><br><br><br></td></tr></table>')
    p.append('<br><br><br><br>')
    p.append('</body>')
    p.append('</html>')

# Makes a page describing why the submission was rejected
def reject_submission(session:Session, message:str, args:List[str]=[], input:str='', output:str='', post_message:str='') -> Mapping[str, Any]:
    p:List[str] = []
    page_start(p, session)
    p.append('<font color="red">Sorry, there was a problem with this submission:</font><br><br>')
    p.append(f'{message}<br><br>')
    if len(args) > 0:
        p.append(f'Args passed in: <pre class="code">{" ".join(args)}</pre><br><br>')
    if len(input) > 0:
        p.append(f'Input fed in: <pre class="code">{input}</pre><br><br>')
    p.append(f'Output: <pre class="code">{output}</pre><br><br>')
    if len(post_message) > 0:
        p.append(post_message)
    p.append('Please fix the issue and resubmit.')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def accept_submission(
        session:Session, 
        submission:Mapping[str,Any], 
        days_late:int, 
        covered_days:int, 
        score:int
) -> Mapping[str,Any]:
    p:List[str] = []
    page_start(p, session)
    p.append('<font color="green">Your submission passed all tests! Your assignment is complete. ')
    p.append(f'Your tentative score is {score}. ')
    if days_late > 0:
        p.append(f'({days_late} days late, {covered_days} of which were excused.) ')
    p.append('<br><br>(Some assignments have parts that need to be checked manually. ')
    p.append('Also, some checks will be made to ensure that submissions were not just designed to fool the autograder. ')
    p.append('So this score may still be adjusted by the grader.)</font>')
    page_end(p)
    return {
        'content': ''.join(p),
    }


def make_login_page(params:Mapping[str, Any], session:Session, dest_page:str, accounts:Dict[str,Any], message:str='') -> Mapping[str, Any]:
    selected_name = params['name'] if 'name' in params else ''
    p:List[str] = []
    page_start(p, session)
    if len(message) > 0:
        p.append(message)
        p.append('<br><br>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post" onsubmit="hash_password(\'password\');">')
    p.append('<table><tr><td>')
    p.append('Name:')
    p.append('</td><td>')
    p.append('<select name="name">')
    p.append(f'<option name="-- Choose your name --" value="bogus">')
    for name in sorted(accounts):
        p.append(f'<option name="{name}" value="{name}"{" selected" if name == selected_name else ""}>{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>Password:</td><td>')
    p.append('<input type="password" name="password" id="password">')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Log in">')
    p.append('</td></tr></table>')
    p.append('</form>')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def require_login(params:Mapping[str, Any], session:Session, dest_page:str, accounts:Dict[str,Any], course_desc:Mapping[str,Any]) -> Mapping[str, Any]:
    # Log in if credentials were provided
    if 'name' in params and 'password' in params:
        try:
            account = accounts[params['name']]
        except:
            return make_login_page(params, session, dest_page, accounts, f'Unrecognized name: {params["name"]}')
        if account['pw'] != params['password']:
            return make_login_page(params, session, dest_page, accounts, f'Incorrect password. (Please contact the instructor if you need to have your password reset.)')
        session.name = params['name']

    # Make sure we are logged in
    if not session.logged_in():
        return make_login_page(params, session, dest_page, accounts)
    try:
        account = accounts[session.name]
    except:
        return make_login_page(params, session, dest_page, accounts, f'Unrecognized account name: {session.name}')
    
    #### At this point we are logged in, so now let's check some operations that require being logged in...

    # Change password
    if 'first' in params and 'second' in params and params['first'] == params['second']:
        account['pw'] = params['first']
        save_accounts(str(course_desc['accounts']), accounts)

    # See if the password needs to be changed
    if account['pw'] == change_me_hash:
        p:List[str] = []
        page_start(p, session)
        if 'first' in params or 'second' in params:
            p.append('The passwords did not match. Please try again.<br><br>')
        p.append('You need to change your password. Please enter a new one (twice):')
        p.append('<form method="post" onsubmit="hash_password(\'first\'); hash_password(\'second\');"')
        p.append('    <br><input type="password" name="first" id="first">')
        p.append('    <br><input type="password" name="second" id="second">')
        p.append('    <br><input type="submit">')
        p.append('</form>')
        page_end(p)
        return {
            'content': ''.join(p),
        }

    return {}

def make_admin_page(params:Mapping[str, Any], session:Session, dest_page:str, accounts:Dict[str,Any], course_desc:Mapping[str,Any]) -> Mapping[str, Any]:
    # Make sure the we are logged in as a TA
    response = require_login(params, session, dest_page, accounts, course_desc)
    if 'content' in response:
        return response
    account = accounts[session.name]
    if (not 'ta' in account) or account['ta'] != 'true':
        return {
            'content': '403 Forbidden'
        }

    # Add a new student
    if 'newstudent' in params:
        if params['newstudent'] in accounts:
            return {
                'content': f'Error, account for {params["newstudent"]} already exists!'
            }
        add_students([ params['newstudent'] ], accounts)
        save_accounts(str(course_desc['accounts']), accounts)
        print(f'Added new student: {params["newstudent"]}')

    # Reset a student's password
    if 'resetme' in params:
        if not params['resetme'] in accounts:
            return {
                'content': f"Error, account for {params['resetme']} not found!"
            }
        student_account = accounts[params['resetme']]
        student_account['pw'] = change_me_hash
        save_accounts(str(course_desc['accounts']), accounts)
        print(f'Reset password for: {params["resetme"]}')

    # Grant late tokens
    if 'addtoks' in params and 'student' in params:
        if not params['student'] in accounts:
            return {
                'content': f"Error, account for {params['student']} not found!"
            }
        student_account = accounts[params['student']]
        student_account['toks'] += int(params['addtoks'])
        save_accounts(str(course_desc['accounts']), accounts)
        print(f'Updated token balance for {params["student"]} to {student_account["toks"]}')

    p:List[str] = []
    page_start(p, session)

    # Form to reset a password
    p.append('<h2>Reset a student\'s password</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post" onsubmit="hash_password(\'password\');">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student whose password to reset:')
    p.append('</td><td>')
    p.append('<select name="resetme">')
    for name in sorted(accounts):
        if (not 'ta' in accounts[name]) or accounts[name]['ta'] != 'true':
            p.append(f'<option name="{name}" value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Reset password!">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Form to add a new student
    p.append('<h2>Add a new student</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post"">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student name:')
    p.append('</td><td>')
    p.append('<input type="text" name="newstudent">')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Add new student">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Form to grant late tokents
    p.append('<h2>Grant late tokens</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to grant tokens to:')
    p.append('</td><td>')
    p.append('<select name="student">')
    for name in sorted(accounts):
        if (not 'ta' in accounts[name]) or accounts[name]['ta'] != 'true':
            p.append(f'<option name="{name}" value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('Number of tokens to grant:')
    p.append('</td><td>')
    p.append('<input type="text" name="addtoks">')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Grant tokens">')
    p.append('</td></tr></table>')
    p.append('</form>')

    page_end(p)
    return {
        'content': ''.join(p),
    }

def make_submission_page(
    params:Mapping[str, Any],
    session:Session,
    course_desc:Mapping[str,Any],
    project_name:str,
    accounts:Dict[str,Any],
    submit_page:str,
    receive_page:str,
) -> Mapping[str, Any]:
    # Make sure the user is logged in
    response = require_login(params, session, submit_page, accounts, course_desc)
    if 'content' in response:
        return response
    account = accounts[session.name]

    # Extract some values
    desc = course_desc['projects'][project_name]
    title = desc['title']
    title_clean = title.replace(' ', '_')
    due_time = desc['due_time']
    course_name = course_desc['course_long']

    # Make sure the student still needs to submit this project
    if title_clean in account and account[title_clean] > 0 and (not 'ta' in account or account['ta'] != 'true'):
        p:List[str] = []
        page_start(p, session)
        p.append(f'You have already received credit for {title}. There is no need to submit it again.')
        page_end(p)
        return {
            'content': ''.join(p),
        }

    # Make the upload form
    p = []
    page_start(p, session)
    p.append(f'<big><b>{course_name}</b></big><br>')
    p.append(f'<big>Submit <b>{title}</b></big><br>')
    p.append(f'Due time: {due_time}<br>')
    now_time = datetime.now()
    p.append(f'Now time: {now_time}<br>')
    tokens = account["toks"]
    p.append(f'Your late token balance: {tokens}<br>')
    p.append('<br>')
    p.append('Please upload your zip file:')
    p.append(f'<form action="{receive_page}" method="post" enctype="multipart/form-data">')
    p.append('    <input type="file" name="filename">')
    p.append('    <input type="submit">')
    p.append('</form>')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def make_log_out_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    session.name = ''
    p:List[str] = []
    page_start(p, session)
    p.append('You are now logged out. Have a nice day!')
    page_end(p)
    return {
        'content': ''.join(p),
    }


def unpack_submission(
        params: Mapping[str, Any],
        session: Session,
        course_desc:Mapping[str,Any],
        project_name:str,
        accounts:Dict[str,Any],
        submit_page:str,
) -> Mapping[str,Any]:
    # Make sure the user is logged in
    response = require_login(params, session, submit_page, accounts, course_desc)
    if 'content' in response:
        return response
    account = accounts[session.name]

    # Compute the number of days late
    submission_grace_seconds = 15 * 60
    seconds_per_day = 24 * 60 * 60
    now_time = datetime.now()
    desc = course_desc['projects'][project_name]
    days_late = max(0, int((((now_time - desc['due_time']).total_seconds() - submission_grace_seconds) // seconds_per_day) + 1))

    # Unpack the submission
    try:
        desc = course_desc['projects'][project_name]
        title = desc['title']
        title_clean = title.replace(' ', '_')
        folder = receive_and_unpack_submission(params, course_desc['course_short'], title_clean, session.name)
    except Exception as e:
        print(traceback.format_exc())
        return {
            'succeeded': False,
            'page': reject_submission(session, str(e)),
        }
    
    return {
        'succeeded': True,
        'account': account,
        'days_late': days_late,
        'folder': folder,
        'title_clean': title_clean,
    }

    

class Job():
    def __init__(self) -> None:
        self.time = datetime.now()
        self.results:Optional[Mapping[str,Any]] = None

jobs:Dict[str,Job] = {}

# Make a redirect page that will check again in a few seconds
def make_working_page(id:str) -> Mapping[str,Any]:
    global jobs
    job = jobs[id]
    elapsed = datetime.now() - job.time

    p:List[str] = []
    p.append('<!DOCTYPE html>')
    p.append('<html><head>')
    p.append('<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">')
    p.append(f'<meta http-equiv="Refresh" content="3; url=\'working.html?job={id}\'" />')
    p.append('<style>')
    p.append('body,center {')
    p.append('  font-family: verdana, tahoma, geneva, sans-serif;')
    p.append('  font-size: 24px;')
    p.append('  background-color:#cacaca;')
    p.append('}')
    p.append('</style>')
    p.append('</head>')
    p.append('<body><table width="800px" align="center" style="background: #ffffff;"><tr><td>')
    p.append('<img src="banner.png"><br>')
    p.append('<br>Thank you. Your submission has been received, and is currently being tested.<br><br>')
    p.append(f'Elapsed time: {elapsed.seconds} seconds')
    p.append('<br><br><br><br></td></tr></table>')
    p.append('<br><br><br><br>')
    p.append('</body>')
    p.append('</html>')
    return {
        'content': ''.join(p),
    }

# Either show the results (if they are ready) or tell the user we are
# working on it and redirect to try again soon
def get_results(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    global jobs
    if not 'job' in params:
        p:List[str] = []
        page_start(p, session)
        p.append('Error: Expected a "job" parameter.')
        page_end(p)
        return {
            'content': ''.join(p),
        }
    id = params['job']
    if not id in jobs:
        p = []
        page_start(p, session)
        p.append(f'Error: job with id {id} not found!')
        page_end(p)
        return {
            'content': ''.join(p),
        }
    job = jobs[id]
    if job.results is None:
        return make_working_page(id)
    return job.results

# Remove any jobs that are really old
def purge_dead_jobs() -> None:
    global jobs
    for id in jobs:
        job = jobs[id]
        if datetime.now() - job.time > timedelta(minutes=30):
            del jobs[id]

# This is the thread that evaluates a submission
def eval_thread(params: Mapping[str, Any], session: Session, eval_func:Callable[[Mapping[str,Any],Session],Mapping[str,Any]], id:str) -> None:
    global jobs
    the_job = jobs[id]
    the_job.results = eval_func(params, session)

# Makes a job id
def make_random_id() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))

# Starts the evaluation thread and tells the user we are working on it
def launch_eval_thread(params: Mapping[str, Any], session: Session, eval_func:Callable[[Mapping[str,Any],Session],Mapping[str,Any]]) -> Mapping[str,Any]:
    global jobs
    id = make_random_id()
    jobs[id] = Job()
    thread = threading.Thread(target=eval_thread, args=(params, session, eval_func, id))
    thread.start()
    purge_dead_jobs()
    return make_working_page(id)

# Consumes course_descs
# Adds page makers for the submit pages and receive pages to the page_makers dictionary
# (This function is rather hard to follow because it uses a nested-closure. Be careful.
# The nested closure is necessary so that unique variable values will be bound to the inner-most functions.)
def generate_submit_and_receive_pages(
        page_makers:Dict[str,Callable[[Mapping[str,Any],Session],Mapping[str,Any]]],
        course_desc:Mapping[str,Any],
        accounts:Dict[str,Any],
) -> None:
    for proj in course_desc['projects']:
        submit_page_name = f'{course_desc["course_short"]}_{proj}_submit.html'
        receive_page_name = f'{course_desc["course_short"]}_{proj}_receive.html'
        def page_maker_factory(proj_short_name:str, submit_page:str, receive_page:str, project_id:str) -> Tuple[Callable[[Mapping[str,Any],Session],Mapping[str,Any]],Callable[[Mapping[str,Any],Session],Mapping[str,Any]]]:
            def make_submit_page(params: Mapping[str, Any], session: Session) -> Mapping[str,Any]:
                return make_submission_page(
                    params,
                    session,
                    course_desc, # from outer closure, but that is okay because it is the same for all projects
                    proj_short_name, # from inner closure
                    accounts, # from outer closure, but that is okay because it is the same for all projects
                    submit_page, # from inner closure
                    receive_page, # from inner closure
                )
            def make_receive_page(params: Mapping[str, Any], session: Session) -> Mapping[str,Any]:
                return launch_eval_thread(
                    params,
                    session,
                    course_desc['projects'][project_id]['evaluator'], # project_id from inner closure. course_desc is from outer closure, but that is okay because it the same for all projects
                )
            return make_submit_page, make_receive_page
        page_makers[submit_page_name], page_makers[receive_page_name] = page_maker_factory(proj, submit_page_name, receive_page_name)
