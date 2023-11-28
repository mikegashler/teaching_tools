import zipfile
import os
from typing import Mapping, Any, List, Dict
from datetime import datetime
from http_daemon import Session, log
import json
from datetime import datetime
import shutil

pf2_proj1_due_time = datetime(year=2023, month=11, day=28, hour=23, minute=59, second=59)
change_me_hash = "ff854dee05ef262a4219cddcdfaff1f149203fd17d6f4db8454bf5f3d75470c3a4d0ee421257a27a5cb76358167fe6d4562d2e25c10ae7ad9c14492178df5551"

accounts:Dict[str,Any]

def load_accounts() -> None:
    global accounts
    with open('pf2_accounts.json', 'r') as f:
        pf2_accounts = f.read()
    accounts = json.loads(pf2_accounts)

def save_accounts() -> None:
    global accounts
    with open('pf2_accounts.json', 'w') as f:
        f.write(json.dumps(accounts, indent=2))

def add_students(names:List[str]) -> None:
    for name in names:
        accounts[name] = {
            'pw': change_me_hash,
            'toks': 20,
        }


launch_script = '''#!/bin/bash
set -e

# Make sure the files are owned by sandbox
sudo chown -R sandbox:sandbox *

# Make sure the script has unix line endings, and is executable
sudo dos2unix -q ./run.bash
sudo chmod 755 ./run.bash

# Launch the "run.bash" script
sudo -u sandbox ./run.bash $* < _input.txt &

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

def run_submission(start_folder:str, args:List[str]=[], input:str='') -> str:
    # Write the input to a file
    with open(os.path.join(start_folder, '_input.txt'), 'w') as f:
        f.write(input)
        f.write('\n\n\n\n\n\n\n\n') # Add a few newlines to flush any superfluous input prompts

    # Put a launch script in the same folder as run.bash
    with open(os.path.join(start_folder, '_launch.bash'), 'w') as f:
        f.write(launch_script)

    # Execute the launch script
    os.system(f'cd {start_folder}; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)} > _output.txt')

    # Read the output
    with open(os.path.join(start_folder, '_output.txt'), 'r') as f:
        output = f.read()
    return output


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
    student = student.replace(' ', '_').replace(',', '_')
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
    ]
    forbidden_extensions = [
        '.o', 
        '.obj', 
        '.class', 
        '.exe', 
        '.ncb', 
        '.suo', 
        '.pcb',
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
                    raise ValueError(f'Your zip file contains a forbidden file: "{filename}".')
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
        p.append(f'Logged in as <b>{session.name}</b>. <a href="pf2_log_out.html">Log out</a>')
    else:
        p.append('(Not currently logged in)')
    p.append('<br><br>')

def page_end(p:List[str]) -> None:
    p.append('<br><br><br><br></td></tr></table>')
    p.append('<br><br><br><br>')
    p.append('</body>')
    p.append('</html>')


# Makes a page describing the submission problem
def make_submission_error_page(text:str, session:Session) -> Mapping[str, Any]:
    p:List[str] = []
    page_start(p, session)
    p.append('There is a problem with this submission:<br>')
    p.append('<font color="red">')
    p.append(text)
    p.append('</font><br><br>')
    p.append('Please fix this issue and resubmit.')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def pf2_proj1_receive(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    due_time = pf2_proj1_due_time

    # Make sure the user is logged in
    if not session.logged_in():
        return make_pf2_login_page(params, session)
    try:
        account = accounts[session.name]
    except:
        return make_pf2_login_page(params, session, f'Unrecognized account name: {session.name}')

    # Make sure the user has enough late tokens
    submission_grace_seconds = 15 * 60
    seconds_per_week = 7 * 24 * 60 * 60
    now_time = datetime.now()
    cost = max(0, (((now_time - due_time).total_seconds() - submission_grace_seconds) // seconds_per_week) + 1)
    tokens = account["toks"]
    if tokens < cost:
        return make_submission_error_page('You do not have enough late tokens to submit this assignment now', session)

    # Unpack the submission
    try:
        start_folder = receive_and_unpack_submission(params, 'pf2', 'proj1', session.name)
    except Exception as e:
        return make_submission_error_page(str(e), session)

    # Run some tests
    try:
        args = ['aaa', 'bbb', 'ccc']
        input = 'Aloysius'
        output = run_submission(start_folder, args, input)
    except Exception as e:
        return make_submission_error_page(str(e), session)
    expected = '''Hello, what is your name?
> Hi, Aloysius, the arguments you passed in were:
arg 1 = aaa
arg 2 = bbb
arg 3 = ccc

I will now count to ten (with zero-indexed values)
i = 0
i = 1
i = 2
i = 3
i = 4
i = 5
i = 6
i = 7
i = 8
i = 9
Thanks for stopping by. Have a nice day!'''


    p:List[str] = []
    page_start(p, session)
    p.append('Here is the output:')
    p.append('<pre class="code">')
    p.append(output)
    p.append('</pre>')
    page_end(p)
    return {
        'content': ''.join(p),
    }



def pf2_send(params:Mapping[str, Any], session:Session, title:str, due_time:datetime, receive_page:str) -> Mapping[str, Any]:
    # Log in if credentials were provided
    if 'name' in params and 'password' in params:
        try:
            account = accounts[params['name']]
        except:
            return make_pf2_login_page(params, session, f'Unrecognized name: {params["name"]}')
        if account['pw'] != params['password']:
            return make_pf2_login_page(params, session, f'Incorrect password. (Please contact the instructor if you need to have your password reset.)')
        session.name = params['name']

    # Make sure we are logged in
    if not session.logged_in():
        return make_pf2_login_page(params, session)
    try:
        account = accounts[session.name]
    except:
        return make_pf2_login_page(params, session, f'Unrecognized account name: {session.name}')

    # Change password
    if 'first' in params and 'second' in params and params['first'] == params['second']:
        account['pw'] = params['first']
        save_accounts()

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

    # Make the upload form
    p = []
    page_start(p, session)
    p.append(f'<big>Submit <b>{title}</b></big><br>')
    p.append(f'Due time: {due_time}<br>')
    now_time = datetime.now()
    p.append(f'Now time: {now_time}<br>')
    tokens = account["toks"]
    p.append(f'Your late token balance: {tokens}<br>')
    cost = max(0, ((now_time - due_time).total_seconds()) // (7 * 24 * 60 * 60) + 1)
    p.append(f'Cost if your submission is accepted now: {cost}<br>')
    if cost > tokens:
        p.append('Unfortunately, you do not have enough remaining late tokens to submit this assignment so late. (You should probably contact the instructor and beg for mercy.)')
    else:
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

def pf2_proj1_send(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return pf2_send(params, session, 'Project 1', pf2_proj1_due_time, 'pf2_proj1_receive.html')

def make_pf2_login_page(params:Mapping[str, Any], session:Session, message:str='') -> Mapping[str, Any]:
    p:List[str] = []
    page_start(p, session)
    if len(message) > 0:
        p.append(message)
        p.append('<br><br>')
    p.append('<form action="pf2_proj1_send.html" method="post" onsubmit="hash_password(\'password\');">')
    p.append('<table><tr><td>')
    p.append('Name:')
    p.append('</td><td>')
    p.append('<select name="name">')
    for name in sorted(accounts):
        p.append(f'<option name="{name}" value="{name}">{name}</option>')
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

def log_out(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    session.name = ''
    return make_pf2_login_page(params, session)

if __name__ == "__main__":
    student_list = '''Albertson, Alice
Barker, Bob
Coville, Cory'''
    names = student_list.split('\n')
    print(names)
    load_accounts()
    add_students(names)
    save_accounts()
