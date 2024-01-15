from typing import Mapping, Any, List, Dict, cast
import json
import shutil
import zipfile
import os
from datetime import datetime
from http_daemon import Session, log

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

launch_script = '''#!/bin/bash
set -e

# Make sure the files are owned by sandbox
sudo chown sandbox:sandbox .
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

# Executes a submission with the specified args and input, and returns its output
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

def make_submission_page(
    params:Mapping[str, Any],
    session:Session,
    course_name:str,
    desc:Mapping[str,Any],
    accounts:Dict[str,Any],
    accounts_filename:str,
    submit_page:str,
    receive_page:str,
) -> Mapping[str, Any]:
    title = desc['title']
    title_clean = title.replace(' ', '_')
    due_time = desc['due_time']

    # Log in if credentials were provided
    if 'name' in params and 'password' in params:
        try:
            account = accounts[params['name']]
        except:
            return make_login_page(params, session, submit_page, accounts, f'Unrecognized name: {params["name"]}')
        if account['pw'] != params['password']:
            return make_login_page(params, session, submit_page, accounts, f'Incorrect password. (Please contact the instructor if you need to have your password reset.)')
        session.name = params['name']

    # Make sure we are logged in
    if not session.logged_in():
        return make_login_page(params, session, submit_page, accounts)
    try:
        account = accounts[session.name]
    except:
        return make_login_page(params, session, submit_page, accounts, f'Unrecognized account name: {session.name}')
    log(f'account={account}')

    # Change password
    if 'first' in params and 'second' in params and params['first'] == params['second']:
        account['pw'] = params['first']
        save_accounts(accounts_filename, accounts)

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

    if title_clean in account and account[title_clean] > 0:
        p = []
        page_start(p, session)
        p.append('You have already received full credit for this assignment. There is no need to submit it again.')
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
        desc:Mapping[str,Any],
        accounts:Dict[str,Any],
) -> Mapping[str,Any]:
    # Make sure the user is logged in
    if not session.logged_in():
        return {
            'succeeded': False,
            'page': make_login_page(params, session, 'pf2_proj1_submit.html', accounts),
        }

    # Find the account
    title:str = str(desc['title'])
    title_clean = title.replace(' ', '_')
    try:
        account = accounts[session.name]
    except:
        return {
            'succeeded': False,
            'page': make_login_page(
                params,
                session,
                'pf2_proj1_submit.html',
                accounts,
                f'Unrecognized account name: {session.name}',
            )
        }

    # Compute the number of days late
    submission_grace_seconds = 15 * 60
    seconds_per_day = 24 * 60 * 60
    now_time = datetime.now()
    days_late = max(0, int((((now_time - desc['due_time']).total_seconds() - submission_grace_seconds) // seconds_per_day) + 1))

    # Unpack the submission
    try:
        folder = receive_and_unpack_submission(params, 'pf2', title_clean, session.name)
    except Exception as e:
        return {
            'succeeded': False,
            'page': make_submission_error_page(str(e), session),
        }
    
    return {
        'succeeded': True,
        'account': account,
        'days_late': days_late,
        'folder': folder,
        'title_clean': title_clean,
    }
