import zipfile
import os
from typing import Mapping, Any, List, Dict
import sys
from datetime import datetime
from http_daemon import Session, log
import json

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
def receive_and_unpack_submission(params: Mapping[str, Any]) -> str:
    # Make sure we received a zip file
    zipfilename = params['filename']
    _, extension = os.path.splitext(zipfilename)
    if not extension == '.zip':
        raise ValueError(f'Expected a file with the extension ".zip". Got "{extension}".')

    # Make a folder for the submission
    assert 'course' in params
    assert 'project' in params
    assert 'student' in params
    course = params['course']
    project = params['project']
    student = params['student']
    t = datetime.now()
    date_stamp = f'{t.year:04}-{t.month:02}-{t.day:02}_{t.hour:02}-{t.minute:02}-{t.second:02}-{t.microsecond:06}.js'
    basename = os.path.join(course, project, student, date_stamp)
    log(f'making dirs: {basename}')
    os.makedirs(basename)
    zipname = os.path.join(basename, os.path.basename(zipfilename))

    # Unzip it
    log(f'moving {zipfilename} to {zipname}')
    os.rename(zipfilename, zipname)
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
    p.append('There is a problem with this submission: ')
    p.append('<font color="red">')
    p.append(text)
    p.append('</font>')
    p.append('Please fix this issue and resubmit.')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def receive_pf2_proj1(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    #print(f'receive_pf2_proj1 was called with params={params}', file=sys.stderr)

    if not session.logged_in():
        return make_pf2_login_page(params, session)

    try:
        start_folder = receive_and_unpack_submission(params)
    except Exception as e:
        return make_submission_error_page(str(e), session)

    try:
        output = run_submission(start_folder, ['aaa', 'bbb', 'ccc'], 'Aloysius')
    except Exception as e:
        return make_submission_error_page(str(e), session)

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

def send_pf2_proj1(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    # Log in if credentials were provided
    if 'name' in params and 'password' in params:
        try:
            account = accounts[params['name']]
        except:
            return make_pf2_login_page(params, session, f'Unrecognized name: {params["name"]}')
        if account['pw'] != params['password']:
            return make_pf2_login_page(params, session, f'Incorrect password')
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
    if account['pw'] == 'change_me':
        p:List[str] = []
        page_start(p, session)
        if 'first' in params or 'second' in params:
            p.append('The passwords did not match. Please try again.<br><br>')
        p.append('You need to change your password. Please enter a new one (twice):')
        p.append('<form method="post"')
        p.append('    <br><input type="password" name="first">')
        p.append('    <br><input type="password" name="second">')
        p.append('    <br><input type="submit">')
        p.append('</form>')
        page_end(p)
        return {
            'content': ''.join(p),
        }

    # Make the upload form
    p = []
    page_start(p, session)
    p.append('Please upload your proj1.zip file:')
    p.append('<form action="pf2_proj1_receive.html" method="post" enctype="multipart/form-data">')
    p.append('    <input type="hidden" name="course" value="pf2">')
    p.append('    <input type="hidden" name="project" value="proj1">')
    p.append('    <input type="hidden" name="student" value="John_Doe">')
    p.append('    <input type="file" name="filename">')
    p.append('    <input type="submit">')
    p.append('</form>')
    page_end(p)
    return {
        'content': ''.join(p),
    }

def make_pf2_login_page(params:Mapping[str, Any], session:Session, message:str='') -> Mapping[str, Any]:
    p:List[str] = []
    page_start(p, session)
    if len(message) > 0:
        p.append(message)
        p.append('<br><br>')
    p.append('<form action="pf2_proj1_send.html" method="post">')
    p.append('<table><tr><td>')
    p.append('Name:')
    p.append('</td><td>')
    p.append('<select name="name">')
    for name in accounts:
        p.append(f'<option name="{name}" value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>Password:</td><td>')
    p.append('<input type="password" name="password">')
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
