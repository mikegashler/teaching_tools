from typing import Mapping, Any, List, Dict, cast, Callable, Optional, Tuple
import json
import shutil
import zipfile
import os
from datetime import datetime, timedelta
from http_daemon import Session, log, maybe_save_state
import traceback
import threading
import random
import string
import sys
from subprocess import STDOUT, check_output, SubprocessError, CalledProcessError

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

launch_script_with_subprocess = '''#!/bin/bash

# Make sure the script has unix line endings, and is executable
sudo dos2unix -q ./run.bash
sudo chmod 755 ./run.bash

# Launch it
./run.bash $* < _stdin.txt

# Clean up some garbage
find . -name ".mypy_cache" -exec rm -rf {} \;
find . -name "__pycache__" -exec rm -rf {} \;
exit 0
'''

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
TIME_LIMIT=8
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
TIME_LIMIT=8
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
        f.write(launch_script_with_subprocess)
        # f.write(launch_script_with_sandbox if sandbox else launch_script_without_sandbox)

    # # Execute the launch script
    # os.system(f'cd {start_folder}; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)} > _stdout.txt 2> _stderr.txt')

    # # Read the output
    # with open(os.path.join(start_folder, '_stdout.txt'), 'r') as f:
    #     stdout = f.read()
    # with open(os.path.join(start_folder, '_stderr.txt'), 'r') as f:
    #     stderr = f.read()
    # return stdout + stderr

    try:
        output = check_output(f'cd {start_folder}; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)}', stderr=STDOUT, shell=True, timeout=10)
    except SubprocessError:
        output = b"error: Timed out. (This usually indicates an endless loop in your code.)"
    except CalledProcessError:
        output = b"error: non-zero return code. (This is probably an error with the submission server.)"
    except:
        output = b"error: unrecognized error."
        print('Unrecognized error:')
        print(traceback.format_exc(), file=sys.stderr)
    max_output_size = 2000000
    return output[:max_output_size].decode()

# Receives a submission. Unzips it. Checks for common problems.
# Executes it, and returns the output as a string.
# Throws a ValueError if anything is wrong with the submission.
def receive_and_unpack_submission(params:Mapping[str, Any], course:str, project:str, student:str) -> str:
    # Make sure we received a zip file
    zipfilename = params['filename']
    _, extension = os.path.splitext(zipfilename)
    if not extension == '.zip':
        raise ValueError(f'Expected a file with the extension ".zip". Got "{extension}".')
    if os.stat(zipfilename).st_size >= 2000000:
        log(f'Received a file named {zipfilename} that was too big ({os.stat(zipfilename).st_size}). Deleting it and aborting.')
        os.remove(zipfilename)
        raise ValueError(f'Expected the zip to be less than 2MB.')

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
            if os.stat(os.path.join(path, filename)).st_size > 2000000:
                msg =f'The file {filename} is too big. All files must be less than 2MB.'
                log(msg)
                raise ValueError(msg)
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
    p.append('  width:750px;')
    p.append('  overflow-x:scroll;')
    p.append('}')
    p.append('</style>')
    p.append('<script src="sha512.js"></script>')
    p.append('<script>\n')
    p.append('function get_session_id() {\n')
    p.append('	let cookie = document.cookie;\n')
    p.append('	const start_pos = cookie.indexOf("sid=") + 4;\n')
    p.append('	if (start_pos < 0) {\n')
    p.append('		console.log("expected a cookie");\n')
    p.append('      return "";\n')
    p.append('	}\n')
    p.append('	const end_pos = cookie.indexOf(";", start_pos);\n')
    p.append('	let sid;\n')
    p.append('	if (end_pos >= 0) {\n')
    p.append('		sid = cookie.substring(start_pos, end_pos);\n')
    p.append('	} else {\n')
    p.append('		sid = cookie.substring(start_pos);\n')
    p.append('	}\n')
    p.append('	return sid;\n')
    p.append('}\n')
    p.append('const g_session_id = get_session_id();\n')
    p.append('</script>')
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

# Loads a file and converts it to a string for displaying in an error message
def display_data(filename:str) -> str:
    p:List[str] = []
    p.append('Data:<br><pre class="code">')
    with open(filename, 'r') as f:
        p.append(f.read())
    p.append('</pre><br><br>')
    return ''.join(p)

# Makes a page describing why the submission was rejected
def reject_submission(
        session:Session, 
        message:str, 
        args:List[str]=[], 
        input:str='', 
        output:str='', 
        post_message:str='') -> Mapping[str, Any]:
    p:List[str] = []
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
    return {
        'results': ''.join(p),
    }

def accept_submission(
        session:Session, 
        submission:Mapping[str,Any], 
        days_late:int, 
        covered_days:int, 
        score:int
) -> Mapping[str,Any]:
    p:List[str] = []
    p.append('<font color="green">Your submission passed all tests! Your assignment is complete. ')
    p.append(f'Your tentative score is {score}. ')
    if days_late + covered_days > 0:
        p.append(f'({days_late + covered_days} days late, {covered_days} of which were excused.) ')
    p.append('<br><br>(Some assignments have parts that need to be checked manually. ')
    p.append('Also, some checks will be made to ensure that submissions were not just designed to fool the autograder. ')
    p.append('So this score may still be adjusted by the grader.)</font>')
    return {
        'results': ''.join(p),
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

# Returns an empy dictionary if the user is already logged in.
# Returns a login page (with the destination set as specified) if the user is not logged in.
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
        maybe_save_state()

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

def make_grades(accounts:Dict[str,Any], course_desc:Mapping[str,Any], student:str) -> str:
    now_time = datetime.now()
    t:List[str] = []
    p:List[str] = []
    p.append('<pre class="code">')

    # Row 1
    t.append('<table border="1" style="overflow-x:scroll; width:700px; display:block;"><tr><td>Last Name</td><td>First Name</td>')
    p.append('Last Name,First Name')
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        proj_title = proj["title"]
        t.append(f'<td>{proj_title}</td>')
        p.append(f',{proj_title}')
    t.append('<td>Grade</td></tr>\n')
    p.append(',Grade')
    p.append('\n')

    # Row 2
    t.append('<tr><td></td><td>Weight</td>')
    p.append(',Weight')
    sum_weight = 0.
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        weight = proj["weight"]
        due_time = proj['due_time']
        if now_time < due_time:
            weight = 0.
        sum_weight += weight
        t.append(f'<td>{weight}</td>')
        p.append(f',{weight}')
    p.append(f'<td>{sum_weight}</td></tr>\n')
    p.append(f',=sum(c2:{chr(98+len(course_desc["projects"]))}2)')
    p.append('\n')

    # Row 3
    t.append('<tr><td></td><td>Possible</td>')
    p.append(',Points possible')
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        proj_points = proj["points"]
        t.append(f'<td>{proj_points}</td>')
        p.append(f',{proj_points}')
    t.append('<td></td></tr>\n')
    p.append('\n')

    # Rows 4 on
    row_index = 4
    for name in accounts:
        if len(student) > 0 and name != student:
            continue
        acc = accounts[name]
        split_name = name.split(',')
        t.append(f'<tr><td>{split_name[0]}</td><td>{split_name[1]}</td>')
        p.append(name)
        eq = '=(0'
        col_index = 99 # 'c'
        weighted_points = 0.
        for proj_id in course_desc['projects']:
            proj = course_desc['projects'][proj_id]
            weight = proj["weight"]
            proj_points = proj["points"]
            proj_title_clean = proj['title'].replace(' ', '_')
            due_time = proj['due_time']
            score = float(acc[proj_title_clean] if proj_title_clean in acc else 0.)
            if proj_title_clean in acc or now_time >= due_time:
                t.append(f'<td>{score}</td>')
                p.append(f',{score}')
                weighted_points += weight * score / proj_points
                eq += f'+{chr(col_index)}2*{chr(col_index)}{row_index}/{chr(col_index)}3'
            else:
                due_str = f'Due {due_time.year}-{due_time.month}-{due_time.day}'
                t.append(f'<td>{due_str}</td>')
                p.append(f',{due_str}')
            col_index += 1
        t.append(f'<td>{weighted_points * 100. / sum_weight}</td></tr>\n')
        eq += f')*100/{chr(col_index)}2'
        p.append(f',{eq}')
        p.append('\n')
        row_index += 1
    t.append('</table>\n')
    p.append('\n')
    p.append('</pre>')
    return f'{"".join(t)}<br><br>And here is a CSV version suitable for pasting in a spreadsheet program:<br>{"".join(p)}'

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

    # Set project score
    if 'project' in params and 'score' in params and 'student' in params:
        if not params['student'] in accounts:
            return {
                'content': f"Error, account for {params['student']} not found!"
            }
        student_account = accounts[params['student']]
        student_account[params['project']] = int(params['score'])
        save_accounts(str(course_desc['accounts']), accounts)
        print(f'Updated score for {params["student"]} {params["project"]} to {params["score"]}')

    # Set many scores
    if 'project' in params and 'scores' in params:
        rows = params['scores'].split('\n')
        for row in rows:
            cells = row.split(',')
            if len(cells) < 1:
                continue
            elif len(cells) != 3:
                return {
                    'content': f"Error on the line {cells}, expected 3 columns"
                }
            student_name = cells[0] + ',' + cells[1]
            if not student_name in accounts:
                return {
                    'content': f"Error, no student named {student_name}"
                }
            try:
                int(cells[2])
            except:
                return {
                    'content': f"Error on the line {cells}, expected the third column to be an integer"
                }
        for row in rows:
            cells = row.split(',')
            if len(cells) < 1:
                continue
            student_name = cells[0] + ',' + cells[1]
            accounts[student_name][params['project']] = int(cells[2])
        save_accounts(str(course_desc['accounts']), accounts)

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

    # Form to grant late tokens
    p.append('<h2>Grant late tokens</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to grant tokens to:')
    p.append('</td><td>')
    p.append('<select name="student">')
    for name in sorted(accounts):
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

    # Form to set project score
    p.append('<h2>Set project score</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to set score for:')
    p.append('</td><td>')
    p.append('<select name="student">')
    for name in sorted(accounts):
        p.append(f'<option name="{name}" value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('Project to set score for:')
    p.append('</td><td>')
    p.append('<select name="project">')
    for proj in course_desc['projects']:
        title = course_desc['projects'][proj]['title']
        title_clean = title.replace(' ', '_')
        p.append(f'<option name="{title_clean}" value="{title_clean}">{title_clean}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('Score to set:')
    p.append('</td><td>')
    p.append('<input type="text" name="score">')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Set score">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Form to set many project scores
    p.append('<h2>Set many project scores</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Project to set score for:')
    p.append('</td><td>')
    p.append('<select name="project">')
    for proj in course_desc['projects']:
        title = course_desc['projects'][proj]['title']
        title_clean = title.replace(' ', '_')
        p.append(f'<option name="{title_clean}" value="{title_clean}">{title_clean}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('CSV data: (last-name, first-name, score)')
    p.append('</td><td>')
    p.append('<textarea name="scores"></textarea>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Set many scores">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Show all the grades
    p.append(make_grades(accounts, course_desc, ''))

    page_end(p)
    return {
        'content': ''.join(p),
    }

def view_scores_page(
    params:Mapping[str, Any],
    session:Session,
    dest_page:str,
    accounts:Dict[str,Any],
    course_desc:Mapping[str,Any],
) -> Mapping[str, Any]:
    response = require_login(params, session, dest_page, accounts, course_desc)
    if 'content' in response:
        return response
    p:List[str] = []
    page_start(p, session)
    p.append(make_grades(accounts, course_desc, session.name))
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

    p:List[str] = []
    page_start(p, session)
    p.append(f'<big><b>{course_name}</b></big><br>')
    p.append(f'<big>Submit <b>{title}</b></big><br>')

    # Make sure the student still needs to submit this project
    if title_clean in account and account[title_clean] > 0 and (not 'ta' in account or account['ta'] != 'true'):
        p.append(f'You have already received credit for {title}. There is no need to submit it again.')
    else:
        # Make the upload form
        p.append(f'Due time: {due_time}<br>')
        now_time = datetime.now()
        p.append(f'Now time: {now_time}<br>')
        tokens = account["toks"]
        p.append(f'Your late token balance: {tokens}<br>')
        p.append('<br>')
        p.append('Please upload your zip file:')
        p.append(f'<form action="{receive_page}" method="post" enctype="multipart/form-data">')
        p.append('    <input type="file" id="file" name="filename">')
        p.append('    <input type="submit">')
        p.append('</form>')
        p.append('<script>\n')
        p.append('const uploadField = document.getElementById("file");\n')
        p.append('uploadField.onchange = function() {\n')
        p.append('    if(this.files[0].size > 2000000){\n')
        p.append('       alert("That file is too big!");\n')
        p.append('       this.value = "";\n')
        p.append('    }\n')
        p.append('}\n')
        p.append('</script>')

    # Make the view scores form
    p.append('<br><br>')
    p.append(f'<a href="{course_desc["course_short"]}_view_scores.html">View your scores</a><br>')

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

# If successful, returns
# {
#   'succeeded': True,
#   ...info about the unpacked submission
# }
# If unsuccessful, returns
# {
#   'succeeded': False,
#   'page': { 'content': some error page }
# }
def unpack_submission(
        params: Mapping[str, Any],
        session: Session,
        course_desc:Mapping[str,Any],
        project_name:str,
        accounts:Dict[str,Any],
        submit_page:str,
) -> Mapping[str,Any]:
    print(f'in unpack_submission for session.name={session.name}', file=sys.stderr)

    # Make sure the user is logged in
    response = require_login(params, session, submit_page, accounts, course_desc)
    if 'content' in response:
        return {
            'succeeded': False,
            'page': response,
        }
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

job_queue:List[Job] = []
jobs:Dict[str,Job] = {}

# Make a redirect page that will check again in a few seconds
def make_working_page(id:str, session: Session) -> Mapping[str,Any]:
    p:List[str] = []
    page_start(p, session)
    p.append('<div id="content">\n')
    p.append('<br>Thank you. Your submission has been received, and is currently being tested.<br><br><pre class="code" id="messages"></pre><br>')
    p.append('</div>\n')
    p.append('<script>\n')
    p.append('let got_results = false;\n')
    p.append('\n')
    p.append('function receive_response(response) {\n')
    p.append('  console.log(`Got response: ${JSON.stringify(response)}`);\n')
    p.append('  if (response.results) {\n')
    p.append('      got_results = true;\n')
    p.append('      console.log(`Got content`);\n')
    p.append('      let content_div = document.getElementById("content");\n')
    p.append('      content_div.innerHTML = response.results;\n')
    p.append('  } else if (response.message) {\n')
    p.append('      let messages = document.getElementById("messages");\n')
    p.append('      messages.innerHTML = messages.innerHTML + response.message + "\\n";\n')
    p.append('  } else {\n')
    p.append('      let msg = "Got a response with no content or message!";\n')
    p.append('      console.log(msg);\n')
    p.append('      let messages = document.getElementById("messages");\n')
    p.append('      messages.innerHTML = messages.innerHTML + response.message + "\\n";\n')
    p.append('  }\n')
    p.append('}\n')
    p.append('\n')
    p.append('function receive_error(ex) {\n')
    p.append('    console.log(`Caught a Javascript error: ${JSON.stringify(ex)}`);\n')
    p.append('    let messages = document.getElementById("messages");\n')
    p.append('    messages.innerHTML = messages.innerHTML + ex + "\\n";\n')
    p.append('}\n')
    p.append('\n')
    p.append('function check_for_results() {\n')
    p.append('  if (got_results) {\n')
    p.append('      return;')
    p.append('  }\n')
    p.append('  console.log("Checking for results...");\n')
    p.append('  fetch("get_results.html", {\n')
    p.append('  	body: JSON.stringify({ id: "' + id + '" }),\n')
    p.append('  	cache: "no-cache",\n')
    p.append('  	headers: {\n')
    p.append("  		'Content-Type': 'application/json',\n")
    p.append("  		'Brownie': `sid=${g_session_id}`,\n")
    p.append('  	},\n')
    p.append('  	method: "POST",\n')
    p.append('  }).then(response => {\n')
    p.append('      return response.json();\n')
    p.append('  }).then(response => {\n')
    p.append('      receive_response(response);\n')
    p.append('  }).catch(ex => {\n')
    p.append('      receive_error(ex);\n')
    p.append('  });\n')
    p.append('}\n')
    p.append('\n')
    p.append('setInterval(check_for_results, 1000);\n')
    p.append('</script>\n')
    page_end(p)
    return {
        'content': ''.join(p),
    }

# This is called by AJAX POST from the make_working_page.
# It returns a JSON object that indicates progress or results
def get_results(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    global jobs
    log(f'in get_results, params={params}')
    if not 'id' in params:
        log('no id')
        return {
            'message': 'Expected a job id in the request'
        }
    id = params['id']
    if not id in jobs:
        log('no job')
        return {
            'message': f'job with id {id} not found!'
        }
    job = jobs[id]
    if job.results is None:
        elapsed = datetime.now() - job.time
        log('not done')
        return {
            'message': f'Still working on it after {elapsed.seconds} seconds'
        }
    log(f'returning results: {job.results}')
    return job.results

# Remove any jobs that are really old
def purge_dead_jobs() -> None:
    global jobs
    for id in list(jobs.keys()):
        if id in jobs:
            job = jobs[id]
            if datetime.now() - job.time > timedelta(minutes=30):
                del jobs[id]

# This is the thread that evaluates a submission
def eval_thread(params: Mapping[str, Any], session: Session, eval_func:Callable[[Mapping[str,Any],Session],Mapping[str,Any]], id:str) -> None:
    global jobs
    print(f'in eval_thread for session.name={session.name}', file=sys.stderr)
    the_job = jobs[id]
    the_job.results = eval_func(params, session)

# Makes a job id
def make_random_id() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))

# Starts the evaluation thread and tells the user we are working on it
def launch_eval_thread(
        params: Mapping[str, Any], 
        session: Session, 
        eval_func:Callable[[Mapping[str,Any],Session],Mapping[str,Any]],
        submit_page:str, 
        accounts:Dict[str,Any],
        course_desc:Mapping[str,Any],
) -> Mapping[str,Any]:
    global jobs

    # Get the account
    response = require_login(params, session, submit_page, accounts, course_desc)
    if 'content' in response:
        return response

    # Make the job
    id = make_random_id()
    jobs[id] = Job()
    thread = threading.Thread(target=eval_thread, args=(params, session, eval_func, id))
    thread.start()
    purge_dead_jobs()
    return make_working_page(id, session)

# Generates functions that handle submitting and receiving project submissions
def page_maker_factory(
        proj_short_name:str, 
        submit_page:str, 
        receive_page:str, 
        course_desc:Mapping[str,Any],
        accounts:Dict[str,Any],
) -> Tuple[Callable[[Mapping[str,Any],Session],Mapping[str,Any]],Callable[[Mapping[str,Any],Session],Mapping[str,Any]]]:
    def make_submit_page(params: Mapping[str, Any], session: Session) -> Mapping[str,Any]:
        return make_submission_page(
            params,
            session,
            course_desc,
            proj_short_name,
            accounts,
            submit_page,
            receive_page,
        )
    def make_receive_page(params: Mapping[str, Any], session: Session) -> Mapping[str,Any]:
        return launch_eval_thread(
            params,
            session,
            course_desc['projects'][proj_short_name]['evaluator'],
            submit_page,
            accounts,
            course_desc,
        )
    return make_submit_page, make_receive_page


# Consumes course_descs
# Adds page makers for the submit pages and receive pages to the page_makers dictionary
def generate_submit_and_receive_pages(
        page_makers:Dict[str,Callable[[Mapping[str,Any],Session],Mapping[str,Any]]],
        course_desc:Mapping[str,Any],
        accounts:Dict[str,Any],
) -> None:
    for proj in course_desc['projects']:
        if 'evaluator' in course_desc['projects'][proj]:
            submit_page_name = f'{course_desc["course_short"]}_{proj}_submit.html'
            receive_page_name = f'{course_desc["course_short"]}_{proj}_receive.html'
            page_makers[submit_page_name], page_makers[receive_page_name] = page_maker_factory(
                proj, 
                submit_page_name, 
                receive_page_name, 
                course_desc,
                accounts,
            )
