from typing import Mapping, Any, List, Dict, cast, Callable, Optional, Tuple
import json
import shutil
import zipfile
import tarfile
import os
from datetime import datetime, timedelta
from http_daemon import log
import traceback
import threading
import random
import string
import sys
import subprocess
from subprocess import STDOUT, SubprocessError, CalledProcessError
import diff
from session import Session, maybe_save_sessions

change_me_hash = "ff854dee05ef262a4219cddcdfaff1f149203fd17d6f4db8454bf5f3d75470c3a4d0ee421257a27a5cb76358167fe6d4562d2e25c10ae7ad9c14492178df5551"

def get_accounts_filename(course_desc:Mapping[str,Any]) -> str:
    return os.path.join(course_desc['course_short'], 'scores.json')

def load_accounts(course_desc:Mapping[str,Any]) -> Dict[str,Any]:
    filename = get_accounts_filename(course_desc)
    print(f'Loading {filename} from {os.getcwd()}')
    with open(filename, 'r') as f:
        accounts = f.read()
    return cast(Dict[str,Any], json.loads(accounts))

def save_accounts(course_desc:Mapping[str,Any], accounts:Dict[str,Any]) -> None:
    os.makedirs(course_desc['course_short'], exist_ok=True)
    filename = get_accounts_filename(course_desc)
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

# Make sure the script has unix line endings, and is executable
dos2unix -q ./run.bash
chmod 755 ./run.bash

# Launch it
./run.bash $* < _stdin.txt

# Clean up some garbage
find . -name ".mypy_cache" -exec rm -rf {} \;
find . -name "__pycache__" -exec rm -rf {} \;
find . -name "*.class" -exec rm -rf {} \;
exit 0
'''

launch_java = '''#!/bin/bash
set -e
javac -Xlint:deprecation *.java
java Main $* < _stdin.txt
find . -name "*.class" -exec rm -rf {} \;
exit 0
'''

launch_nodejs = '''#!/bin/bash
set -e
node server.js < _stdin.txt
find . -name "*.png" -exec rm -rf {} \;
exit 0
'''

# Executes a submission with the specified args and input, and returns its output
def run_submission(submission:Mapping[str,Any], args:List[str]=[], input:str='', sandbox:bool=True) -> str:
    # Write the input to a file
    start_folder = submission['folder']
    with open(os.path.join(start_folder, '_stdin.txt'), 'w') as f:
        f.write(input)
        f.write('\n\n0\n\n0\n\n0\n\n') # Add a few extra lines to flush any superfluous input prompts

    # Put a launch script in the same folder as run.bash
    with open(os.path.join(start_folder, '_launch.bash'), 'w') as f:
        f.write(launch_script)

    try:
        # Launch it
        if sandbox:
            subprocess.run(f'cd "{start_folder}"; chown sandbox:sandbox .; chown -R sandbox:sandbox *; chmod 755 _launch.bash', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=5)
            cp = subprocess.run(f'cd "{start_folder}"; runuser -u sandbox ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
        else:
            cp = subprocess.run(f'cd "{start_folder}"; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
    except CalledProcessError as cpe:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: non-zero return code. (Your program should return 0 if it is successful.): {str(cpe)}")
    except SubprocessError as se:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: Timed out. (This usually indicates an endless loop in your code.): {str(se)}")
    except Exception as e:
        output = b"error: unrecognized error."
        print('Unrecognized error:')
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"Unrecognized error: {str(e)}")

    # Clean the output
    max_output_size = 16000000
    cleaned_output = output[:max_output_size].decode()
    cleaned_output = cleaned_output.replace('Success: no issues found ', 'MyPy found no typing issues ')
    cleaned_output = cleaned_output.replace('find: ‘./.mypy_cache’: No such file or directory', '')
    cleaned_output = cleaned_output.replace('find: ‘./__pycache__’: No such file or directory', '')
    return cleaned_output

# Injects a little code into Controller.java to give us control of the GUI
def infect_controller(
    file_string:str,
    imports_to_inject:str,
    classes_to_inject:str,
    member_variables_to_inject:str,
    initializers_to_inject:str,
    update_code_to_inject:str,
) -> str:
    # Add some boiler plate code
    imports_to_inject += '''
import java.util.ArrayList;
import java.awt.Image;
import java.io.PrintWriter;
import java.awt.Component;
'''
    classes_to_inject += '''
'''
    member_variables_to_inject += '''
    static Controller ag_controller = null;
    int ag_frame_count;
    boolean ag_screen_cleared;
    ArrayList<AGSprite> ag_sprites;
    Image ag_first_selected_image;
    Image ag_second_selected_image;
    Image ag_third_selected_image;

    void ag_add_sprite(Image image, int x, int y, int w, int h)
    {
        this.ag_sprites.add(new AGSprite(image, x, y, w, h));
    }

    // Returns the first button in the list of components in the view that contains
    // any of the specified strings in its text
    JButton ag_find_button(String[] strings)
    {
        for (int i = 0; i < this.view.components.size(); i++) {
            Component comp = this.view.components.get(i);
            for (int j = 0; j < strings.length; j++) {
                if (comp instanceof JButton) {
                    if (((JButton)comp).getText().toLowerCase().contains(strings[j].toLowerCase()))
                        return (JButton)comp;
                }
            }
        }
        return null;
    }

    // Returns the sprite with a bottom-middle closest to the specified coordinates (or null if there are none)
    // If x or y is Integer.MAX_VALUE, then it will be ignored.
    AGSprite ag_find_sprite(int x, int y)
    {
        double best_dist = Double.MAX_VALUE;
        AGSprite best_image = null;
        for (int i = 0; i < this.ag_sprites.size(); i++)
        {
            AGSprite im = this.ag_sprites.get(i);
            int imx = im.bx();
            int imy = im.by();
            int xx = x;
            int yy = y;
            if (xx == Integer.MAX_VALUE)
                xx = imx;
            if (yy == Integer.MAX_VALUE)
                yy = imy;
            double sq_dist = (imy - yy) * (imy - yy) + (imx - xx) * (imx - xx);
            if (sq_dist < best_dist)
            {
                best_dist = sq_dist;
                best_image = im;
            }
        }
        if (best_image != null)
            System.out.println("[autograder] Searched for image near (" + (x == Integer.MAX_VALUE ? "?" : Integer.toString(x)) + "," + (y == Integer.MAX_VALUE ? "?" : Integer.toString(y)) + "). Found sprite at (" + Integer.toString(best_image.bx()) + ", " + Integer.toString(best_image.by()) + ") on frame " + Integer.toString(this.ag_frame_count));
        return best_image;
    }

    void ag_terminate(String result)
    {
        try {
            PrintWriter writer = new PrintWriter("ag_result.txt", "UTF-8");
            writer.println(result);
            writer.close();
        } catch (Exception e) {
            System.out.print("An exception was thrown: " + e.toString());
        }
        System.exit(0);
    }

    void ag_click(int x, int y, int button)
    {
        System.out.println("[autograder] Clicked mouse button " + Integer.toString(button) + " at " + Integer.toString(x) + ", " + Integer.toString(y) + " on frame " + Integer.toString(this.ag_frame_count));
        MouseEvent event = new MouseEvent(JPanel.click_me, 0, 0, 0, x, y, 0, false, button);
        this.mouseClicked(event);
        this.mousePressed(event);
        this.mouseReleased(event);
    }

    void ag_press_key(int key, char keychar)
    {
        System.out.println("[autograder] Pressed key " + Integer.toString(key) + " on frame " + Integer.toString(this.ag_frame_count));
        KeyEvent event = new KeyEvent(JPanel.click_me, 0, 0, 0, key, keychar);
        this.keyPressed(event);
    }

    void ag_release_key(int key, char keychar)
    {
        System.out.println("[autograder] Released key " + Integer.toString(key) + " on frame " + Integer.toString(this.ag_frame_count));
        KeyEvent event = new KeyEvent(JPanel.click_me, 0, 0, 0, key, keychar);
        this.keyReleased(event);
    }

    // Print all the images
    void ag_print_images()
    {
        System.out.println("[autograder] images on screen at frame count " + Integer.toString(this.ag_frame_count));
        for (int i = 0; i < this.ag_sprites.size(); i++)
        {
            AGSprite sprite = this.ag_sprites.get(i);
            System.out.println("[autograder]    " + Integer.toString(i) + ": botmid=(" + Integer.toString(sprite.bx()) + "," + Integer.toString(sprite.by()) + "), topleft=(" + Integer.toString(sprite.x) + ", " + Integer.toString(sprite.y) + "), src_widhgt=(" + Integer.toString(sprite.image.getWidth(null)) + "," + Integer.toString(sprite.image.getHeight(null)) + "), dst_widhgt=(" + Integer.toString(sprite.w) + "," + Integer.toString(sprite.h) + ")");
        }
    }

'''
    initializers_to_inject += '''
        Controller.ag_controller = this;
        this.ag_frame_count = 0;
        ag_screen_cleared = false;
        this.ag_sprites = new ArrayList<AGSprite>();
'''
    update_code_to_inject += '''

            // Reset stuff
            this.ag_frame_count++;
            this.ag_screen_cleared = false;
            this.ag_sprites.clear();
'''

    # Find the spots in Controller.java where we can inject our code
    class_controller_pos = file_string.find('class Controller')
    if class_controller_pos < 0:
        raise RejectSubmission('Expected Controller.java to contain "class Controller"', [], '', '')
    class_start_pos = file_string.find('{', class_controller_pos)
    if class_start_pos < 0:
        raise RejectSubmission('Expected a "{" after "class Controller"', [], '', '')
    constructor_sig_pos = file_string.find('Controller(', class_start_pos)
    if constructor_sig_pos < 0:
        raise RejectSubmission('Expected "Controller(" to occur in class Controller', [], '', '')
    constructor_start_pos = file_string.find('{', constructor_sig_pos)
    if constructor_start_pos < 0:
        raise RejectSubmission('Expected a "{" after "Controller("', [], '', '')
    update_sig_pos = file_string.find(' update(', class_start_pos)
    if update_sig_pos < 0:
        raise RejectSubmission('Expected " update(" to occur in class Controller', [], '', '')
    update_start_pos = file_string.find('{', update_sig_pos)
    if update_start_pos < 0:
        raise RejectSubmission('Expected a "{" after "void update()"', [], '', '')

    # Inject it
    class_start_pos += 1
    constructor_start_pos += 1
    update_start_pos += 1
    if update_start_pos > constructor_start_pos:
        file_string = imports_to_inject + file_string[:class_controller_pos] + classes_to_inject + file_string[class_controller_pos:class_start_pos] + member_variables_to_inject + file_string[class_start_pos:constructor_start_pos] + initializers_to_inject + file_string[constructor_start_pos:update_start_pos] + update_code_to_inject + file_string[update_start_pos:]
    else:
        file_string = imports_to_inject + file_string[:class_controller_pos] + classes_to_inject + file_string[class_controller_pos:class_start_pos] + member_variables_to_inject + file_string[class_start_pos:update_start_pos] + update_code_to_inject + file_string[update_start_pos:constructor_start_pos] + initializers_to_inject + file_string[constructor_start_pos:]
    return file_string

# A special-purpose version of run_submission for Java programs in Programming Paradigms
# that use a particular model-view-controller GUI interface.
def run_java_gui_submission(
    submission:Mapping[str,Any],
    args:List[str]=[],
    input:str='',
    sandbox:bool=True,
    imports_to_inject:str='',
    classes_to_inject:str='',
    member_variables_to_inject:str='',
    initializers_to_inject:str='',
    update_code_to_inject:str='',
) -> str:
    input = ''
    start_folder = submission['folder']
    controller_build_me = os.path.join(start_folder, 'Controller.java')
    controller_hack_me = os.path.join(start_folder, 'Controller.hack_me')
    if not os.path.exists(controller_hack_me):
        # Touch up all java files to remove imports we intend to override
        for fn in os.listdir(submission['folder']):
            _, ext = os.path.splitext(fn)
            if ext == '.java':
                full_path = os.path.join(submission['folder'], fn)
                with open(full_path, 'r') as f:
                    file_string = f.read()
                    file_string = file_string.replace('import javax.swing.JFrame;', '//import javax.swing.JFrame;')
                    file_string = file_string.replace('import javax.swing.JPanel;', '//import javax.swing.JPanel;')
                    file_string = file_string.replace('import java.awt.Graphics2D;', '//import java.awt.Graphics2D;')
                    file_string = file_string.replace('import java.awt.Graphics;', '//import java.awt.Graphics;')
                    file_string = file_string.replace('import java.awt.Toolkit;', '//import java.awt.Toolkit;')
                    file_string = file_string.replace('import javax.swing.JButton;', '//import javax.swing.JButton;')
                with open(full_path, 'w') as f2:
                    f2.write(file_string)
                print(f'rewrote {full_path}')

        # Add java_gui_checker files
        java_gui_checker_path = 'back_end/java_gui_checker'
        for fn in os.listdir(java_gui_checker_path):
            src_path = os.path.join(java_gui_checker_path, fn)
            dst_path = os.path.join(submission['folder'], fn)
            shutil.copyfile(src_path, dst_path)

        # Backup Controller.java (since we are going to infect it with checking code)
        if os.path.exists(controller_build_me):
            shutil.copyfile(controller_build_me, controller_hack_me)
        else:
            raise RejectSubmission('Expected a file named Controller.java in the same folder as run.bash', args, input, '')
        if not os.path.exists(controller_hack_me):
            raise RejectSubmission('Internal error: Failed to back up Controller.java', args, input, '')

    # Infect Controller.java with checking code
    with open(controller_hack_me, 'r') as f:
        file_string = f.read()
    file_string = infect_controller(file_string, imports_to_inject, classes_to_inject, member_variables_to_inject, initializers_to_inject, update_code_to_inject)
    with open(controller_build_me, 'w') as f2:
        f2.write(file_string)

    # Write the input to a file
    with open(os.path.join(start_folder, '_stdin.txt'), 'w') as f:
        f.write(input)
        f.write('\n\n0\n\n0\n\n0\n\n') # Add a few extra lines to flush any superfluous input prompts

    # Put a launch script in the same folder as run.bash
    with open(os.path.join(start_folder, '_launch.bash'), 'w') as f:
        f.write(launch_java)

    try:
        # Launch it
        if sandbox:
            subprocess.run(f'cd "{start_folder}"; chown sandbox:sandbox .; chown -R sandbox:sandbox *; chmod 755 _launch.bash', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=5)
            cp = subprocess.run(f'cd "{start_folder}"; runuser -u sandbox ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
        else:
            cp = subprocess.run(f'cd "{start_folder}"; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
    except CalledProcessError as cpe:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: non-zero return code. (Your program should return 0 if it is successful.): {str(cpe)}")
    except SubprocessError as se:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: Timed out. (This usually indicates an endless loop in your code.): {str(se)}")
    except Exception as e:
        output = b"error: unrecognized error."
        print('Unrecognized error:')
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"Unrecognized error: {str(e)}")

    # Clean the output
    max_output_size = 2000000
    cleaned_output = output[:max_output_size].decode()
    return cleaned_output

# A special-purpose version of run_submission for client-server programs that run in NodeJS
def run_nodejs_submission(
    submission:Mapping[str,Any],
    args:List[str]=[],
    input:str='',
    sandbox:bool=True,
    code_to_inject:str='',
) -> str:
    input = ''
    start_folder = submission['folder']
    server_build_me = os.path.join(start_folder, 'server.js')
    server_hack_me = os.path.join(start_folder, 'server.hack_me')
    if not os.path.exists(server_hack_me):
        # Backup server.js (since we are going to infect it with checking code)
        if os.path.exists(server_build_me):
            shutil.copyfile(server_build_me, server_hack_me)
        else:
            raise RejectSubmission('Expected a file named server.js in the same folder as run.bash', args, input, '')
        if not os.path.exists(server_hack_me):
            raise RejectSubmission('Internal error: Failed to back up server.js', args, input, '')

    # Infect server.js with checking code
    with open(server_hack_me, 'r') as f:
        file_string = f.read()
    file_string += '\n\n\n\n\n\n' + code_to_inject;
    with open(server_build_me, 'w') as f2:
        f2.write(file_string)

    # Write the input to a file
    with open(os.path.join(start_folder, '_stdin.txt'), 'w') as f:
        f.write(input)
        f.write('\n\n0\n\n0\n\n0\n\n') # Add a few extra lines to flush any superfluous input prompts

    # Put a launch script in the same folder as run.bash
    with open(os.path.join(start_folder, '_launch.bash'), 'w') as f:
        f.write(launch_nodejs)

    try:
        # Launch it
        if sandbox:
            subprocess.run(f'cd "{start_folder}"; chown sandbox:sandbox .; chown -R sandbox:sandbox *; chmod 755 _launch.bash', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=5)
            cp = subprocess.run(f'cd "{start_folder}"; runuser -u sandbox ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
        else:
            cp = subprocess.run(f'cd "{start_folder}"; chmod 755 _launch.bash; ./_launch.bash {" ".join(args)}', stdout=subprocess.PIPE, stderr=STDOUT, shell=True, timeout=30)
            output = cp.stdout
    except CalledProcessError as cpe:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: non-zero return code. (Your program should return 0 if it is successful.): {str(cpe)}")
    except SubprocessError as se:
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"error: Timed out. (This usually indicates an endless loop in your code.): {str(se)}")
    except Exception as e:
        output = b"error: unrecognized error."
        print('Unrecognized error:')
        print(traceback.format_exc(), file=sys.stderr)
        raise RejectSubmission('There was an error running this submission', args, input, f"Unrecognized error: {str(e)}")

    # Clean the output
    max_output_size = 2000000
    cleaned_output = output[:max_output_size].decode()
    return cleaned_output

# Receives a submission. Unzips it. Checks for common problems.
# Executes it, and returns the output as a string.
# Throws a ValueError if anything is wrong with the submission.
def unpack_submission(params:Mapping[str, Any], course:str, project_id:str, student:str) -> Tuple[str, str]:
    # Make sure we received a zip file
    zipfilename = params['filename']
    _, extension = os.path.splitext(zipfilename)
    if extension == '.zip' or extension == '.gz' or extension == '.tgz' or extension == '.bz2':
        pass
    else:
        raise ValueError(f'Expected a file with the extension ".zip" or ".gz" or ".tgz" or ".bz2". Got "{extension}".')
    if os.stat(zipfilename).st_size >= 2000000:
        log(f'Received a file named {zipfilename} that was too big ({os.stat(zipfilename).st_size}). Deleting it and aborting.')
        os.remove(zipfilename)
        raise ValueError(f'Expected the zip or tarball to be less than 2MB.')

    # Make a folder for the submission
    t = datetime.now()
    date_stamp = f'{t.year:04}-{t.month:02}-{t.day:02}_{t.hour:02}-{t.minute:02}-{t.second:02}-{t.microsecond:06}'
    student = student.replace(' ', '_').replace(',', '_').replace('\'', '_')
    basename = os.path.join(course, project_id, student, date_stamp)
    os.makedirs(basename)
    zipname = os.path.join(basename, os.path.basename(zipfilename))

    # Unzip it
    shutil.move(zipfilename, zipname)
    if extension == '.zip':
        with zipfile.ZipFile(zipname, 'r') as zip_ref:
            zip_ref.extractall(basename)
    elif extension == '.gz' or extension == '.tgz' or extension == '.bz2':
        with tarfile.open(zipname) as tar_ref: 
            tar_ref.extractall(basename)
    else:
        raise ValueError(f'Unsupported extension: {extension}')

    # Convert back-slashes to forward-slashes (because some Windows zip utilities have a bug
    # that improperly encodes backslashes into the path in voliation of the zip specification)
    filenames = [ fn for fn in os.listdir(basename) if os.path.isfile(os.path.join(basename, fn)) ]
    for fn in filenames:
        if fn.find('\\') >= 0:
            fn_fixed = fn.replace('\\', '/')
            last_slash_index = fn_fixed.rfind('/')
            dest_path = os.path.join(basename, fn_fixed[:last_slash_index])
            os.makedirs(dest_path, exist_ok=True)
            orig_fn = os.path.join(basename, fn)
            dest_fn = os.path.join(dest_path, fn_fixed[last_slash_index+1:])
            os.rename(orig_fn, dest_fn) # does not work with '\\'

    # Find the "run.bash" file
    start_folder = ''
    for path, folders, files in os.walk(basename):
        if 'run.bash' in files:
            if len(start_folder) > 0:
                raise ValueError(f'Multiple "run.bash" files were found in your submission. There should be only one.')
            start_folder = path
    if start_folder == '':
        raise ValueError(f'No "run.bash" file was found in your submission.')
    return basename, start_folder

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

class RejectSubmission(RuntimeError):
    def __init__(self, message:str, args:List[str], input:str, output:str, extra:str='') -> None:
        super().__init__(message)
        self._args = args
        self.input = input
        self.output = output
        self.extra = extra

def accept_submission(
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

    # Save the feedback
    results = ''.join(p)
    start_folder = submission['folder']
    with open(os.path.join(start_folder, '_feedback.txt'), 'w') as f:
        f.write(results)

    return {
        'results': results,
    }


def make_login_page(params:Mapping[str, Any], session:Session, dest_page:str, accounts:Dict[str,Any], message:str='') -> Mapping[str, Any]:
    selected_name = params['name'] if 'name' in params else ''
    p:List[str] = []
    page_start(p, session)
    if len(message) > 0:
        p.append(message)
        p.append('<br><br>')

    if len(accounts) == 0:
        # Make instructor account
        p.append('<h1>Initial setup</h1>')
        p.append('Welcome, professor. Please enter your name and the password you would like to use for your administrative account:<br>')
        p.append(f'<form action="{dest_page}"')
        p.append(' method="post" onsubmit="hash_password(\'password\');">')
        p.append('<table><tr><td>')
        p.append('First name:')
        p.append('</td><td>')
        p.append('<input type="input" name="prof_first">')
        p.append('</td></tr>')
        p.append('<tr><td>')
        p.append('Last name:')
        p.append('</td><td>')
        p.append('<input type="input" name="prof_last">')
        p.append('</td></tr>')
        p.append('<tr><td>Password:</td><td>')
        p.append('<input type="password" name="password" id="password">')
        p.append('</td></tr>')
        p.append('<tr><td></td><td><input type="submit" value="Create new account">')
        p.append('</td></tr></table>')
        p.append('</form>')
    else:
        # Show login form
        p.append(f'<form action="{dest_page}"')
        p.append(' method="post" onsubmit="hash_password(\'password\');">')
        p.append('<table><tr><td>')
        p.append('Name:')
        p.append('</td><td>')
        p.append('<select name="name">')
        p.append(f'<option value="bogus">-- Choose your name --</option>')
        for name in sorted(accounts):
            p.append(f'<option value="{name}"{" selected" if name == selected_name else ""}>{name}</option>')
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
    if 'name' in params and 'password' in params:
        # Log in
        try:
            account = accounts[params['name']]
        except:
            return make_login_page(params, session, dest_page, accounts, f'Unrecognized name: {params["name"]}')
        if account['pw'] != params['password']:
            return make_login_page(params, session, dest_page, accounts, f'Incorrect password. (Please contact the instructor if you need to have your password reset.)')
        session.name = params['name']
        maybe_save_sessions()
    elif 'prof_first' in params and 'prof_last' in params and 'password' in params and len(accounts) == 0:
        # Make the professor account
        prof_name = f'{params["prof_last"]}, {params["prof_first"]}'
        pw_hash = params['password']
        accounts[prof_name] = {
            'pw': pw_hash,
            'ta': 'true',
            'toks': 0,
        }
        session.name = prof_name
        maybe_save_sessions()
        save_accounts(course_desc, accounts)

    # Make sure we are logged in
    if not session.logged_in():
        return make_login_page(params, session, dest_page, accounts)
    try:
        account = accounts[session.name]
    except:
        return make_login_page(params, session, dest_page, accounts, f'Unrecognized account name: {session.name}')
    
    #### At this point we are definitely logged in,
    #### so now let's check some operations that require being logged in...

    # Change password
    if 'first' in params and 'second' in params and params['first'] == params['second']:
        account['pw'] = params['first']
        save_accounts(course_desc, accounts)

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

def make_project_completion_rates(accounts:Dict[str,Any], course_desc:Mapping[str,Any]) -> str:
    p:List[str] = []
    p.append('<table cellpadding="10px">')
    p.append(f'<tr><td><b><u>Proj name</u></b></td><td><b><u>Due date</u></b></td><td><b><u># complete</u></b></td><td><b><u>% complete</u></b></td></tr>')
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        proj_title = proj['title']
        due_time = proj['due_time']
        due_str = f'{due_time.year}-{due_time.month}-{due_time.day}'
        total_count = 0
        completed_count = 0
        for name in accounts:
            acc = accounts[name]
            if 'ta' in acc:
                continue
            total_count += 1
            if proj_id in acc:
                completed_count += 1
        submit_link = f'<a href="{course_desc["course_short"]}_{proj_id}_submit.html">{proj_title}</a>' if 'evaluator' in proj else proj_title
        completed_perc = '0'
        if total_count > 0:
            completed_perc = f'{(100 * completed_count / total_count):.1f}'
        p.append(f'<tr><td>{submit_link}</td><td>{due_str}</td><td>{completed_count}</td><td>{completed_perc}%</td></tr>')
    p.append('</table>')
    return "".join(p)

def make_grades(accounts:Dict[str,Any], course_desc:Mapping[str,Any], student:str) -> str:
    now_time = datetime.now()
    t:List[str] = []
    p:List[str] = []
    p.append('<pre class="code">')

    # Row 1
    t.append('<table border="1" style="overflow-x:scroll; width:750px; display:block;"><tr><td>Last Name</td><td>First Name</td>')
    p.append('Last Name,First Name')
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        proj_title = proj["title"]
        t.append(f'<td>{proj_title}</td>')
        p.append(f',{proj_title}')
    t.append('<td>Grade</td>')
    #t.append('<td>Letter grade</td>')
    t.append('</tr>\n')
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
    t.append(f'<td><!--{sum_weight}--></td></tr>\n')
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

    # Row 4
    t.append('<tr><td></td><td>Due date</td>')
    p.append(',Due date')
    for proj_id in course_desc['projects']:
        proj = course_desc['projects'][proj_id]
        due_time = proj['due_time']
        due_str = f'{due_time.year}-{due_time.month}-{due_time.day}'
        t.append(f'<td>{due_str}</td>')
        p.append(f',{due_str}')
    t.append('<td></td></tr>\n')
    p.append('\n')

    # Rows 5 on
    row_index = 5
    names = sorted(accounts.keys())
    for name in names:
        if len(student) > 0 and name != student:
            continue
        acc = accounts[name]
        split_name = name.split(',')
        t.append(f'<tr><td>{split_name[0] if len(split_name) > 0 else "???"}</td><td>{split_name[1] if len(split_name) > 1 else "???"}</td>')
        p.append(name)
        eq = '=(0'
        col_index = 99 # 'c'
        weighted_points = 0.
        for proj_id in course_desc['projects']:
            proj = course_desc['projects'][proj_id]
            weight = proj["weight"]
            due_time = proj['due_time']
            if now_time < due_time:
                weight = 0.
            proj_points = proj["points"]
            score = float(acc[proj_id] if proj_id in acc else 0.)
            eq += f'+{chr(col_index)}2*{chr(col_index)}{row_index}/{chr(col_index)}3'
            if proj_id in acc or now_time >= due_time:
                t.append(f'<td>{score}</td>')
                p.append(f',{score}')
                weighted_points += weight * score / max(1, proj_points)
            else:
                t.append(f'<td></td>')
                p.append(f',')
            col_index += 1
        t.append(f'<td>{(weighted_points * 100. / max(1, sum_weight)):.2f}</td></tr>\n')
        eq += f')*100/{chr(col_index)}2'
        p.append(f',{eq}')
        final_score_cell = f'{chr(col_index)}{row_index}'
        #p.append(f',=IF({final_score_cell}>=90,"A",IF({final_score_cell}>=80,"B",IF({final_score_cell}>=70,"C",IF({final_score_cell}>=60,"D","F"))))')
        p.append('\n')
        row_index += 1
    t.append('</table>\n')
    p.append('\n')
    p.append('</pre>')
    return f'{"".join(t)}<br><br>And here is a CSV version suitable for pasting in a spreadsheet program:<br>{"".join(p)}'

def canonicalize_names(rows:List[str], student_names:List[str]) -> str:
    indexes = [ i for i in range(len(rows)) ]
    output = ['\n'] * len(rows)
    while len(rows) > 0 and len(student_names) > 0:
        best_i = 0
        best_j = 0
        best_dist = 1000000
        for i in range(len(rows)):
            for j in range(len(student_names)):
                dist = diff.str_dist(rows[i], student_names[j])
                if dist < best_dist:
                    best_dist = dist
                    best_i = i
                    best_j = j
        index = indexes[best_i]
        output[index] = rows[best_i].strip() + ',' + student_names[best_j]
        del rows[best_i]
        del indexes[best_i]
        del student_names[best_j]
    while len(rows) > 0:
        index = indexes[0]
        output[index] = rows[0] + ',???'
        del rows[0]
        del indexes[0]
    return '\n'.join(output)

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

    p:List[str] = []
    page_start(p, session)

    ###############
    #   Actions   #
    ###############
    print(f'params={params}')

    # View scores action
    if 'scores' in params:
        student = params['scores']
        if student == 'entire_class':
            student = ''
        p.append(make_grades(accounts, course_desc, student))
        page_end(p)
        return {
            'content': ''.join(p),
        }

    # Add new students action
    if 'newstudents' in params:
        rows = params['newstudents'].split('\n')
        for row in rows:
            name = row.strip()
            if len(name) == 0:
                continue
            first_comma = name.find(',')
            if first_comma < 0:
                return {
                    'content': f'Error, one or more names contained no comma'
                }
            if name.rfind(',') != first_comma:
                return {
                    'content': f'Error, one or more names contained multiple commas'
                }
        names_to_add = []
        for row in rows:
            name = row.strip()
            if len(name) == 0:
                continue
            if name in accounts:
                p.append('Skipping {name} because an account for that name already exists<br><br>')
            names_to_add.append(name)
        add_students(names_to_add, accounts)
        save_accounts(course_desc, accounts)
        print(f'{len(names_to_add)} new student accounts created.<br><br>')

    # Reset password action
    if 'resetme' in params:
        if not params['resetme'] in accounts:
            return {
                'content': f"Error, account for {params['resetme']} not found!"
            }
        student_account = accounts[params['resetme']]
        student_account['pw'] = change_me_hash
        save_accounts(course_desc, accounts)
        print(f'Reset password for: {params["resetme"]}')

    # Grant late tokens action
    if 'addtoks' in params and 'student' in params:
        if not params['student'] in accounts:
            return {
                'content': f"Error, account for {params['student']} not found!"
            }
        student_account = accounts[params['student']]
        student_account['toks'] += int(params['addtoks'])
        save_accounts(course_desc, accounts)
        print(f'Updated token balance for {params["student"]} to {student_account["toks"]}')

    # Set project score action
    if 'project' in params and 'score' in params and 'student' in params:
        if not params['student'] in accounts:
            return {
                'content': f"Error, account for {params['student']} not found!"
            }
        student_account = accounts[params['student']]
        student_account[params['project']] = int(params['score'])
        save_accounts(course_desc, accounts)
        print(f'Updated score for {params["student"]} {params["project"]} to {params["score"]}')

    # Impersonate action
    if 'impersonate' in params:
        session.name = params['impersonate']
        p.append(f'You are now impersonating {session.name}<br><br>')

    # Set multiple scores action
    if 'project' in params and 'set_scores' in params:
        rows = params['set_scores'].split('\n')
        for zline, row in enumerate(rows):
            cells = row.split(',')
            if len(cells) < 1 or (len(cells) == 1 and len(cells[0]) < 1):
                continue
            elif len(cells) != 3:
                return {
                    'content': f"Error on the line {zline+1} ({row}), expected 3 columns"
                }
            student_name = cells[0] + ',' + cells[1]
            if not student_name in accounts:
                return {
                    'content': f"Error, no student named {student_name}"
                }
            try:
                float(cells[2])
            except:
                return {
                    'content': f"Error on the line {zline+1} ({row}), expected the third column to be a number"
                }
        for row in rows:
            cells = row.split(',')
            if len(cells) < 1 or (len(cells) == 1 and len(cells[0]) < 1):
                continue
            student_name = cells[0] + ',' + cells[1]
            accounts[student_name][params['project']] = float(cells[2])
        save_accounts(course_desc, accounts)

    # Canonicalize names action
    if 'student_names' in params:
        rows = params['student_names'].split('\n')
        output = '<br><pre class="code">' + canonicalize_names(rows, list(accounts.keys())) + '</pre><br><br>'
        p.append(output)

    # Make TA action
    if 'maketa' in params:
        if not params['maketa'] in accounts:
            return {
                'content': f"Error, account for {params['maketa']} not found!"
            }
        student_account = accounts[params['maketa']]
        student_account['ta'] = 'true'
        save_accounts(course_desc, accounts)
        print(f'Granted TA authority to {params["resetme"]}')



    #############
    #   Stats   #
    #############

    p.append(f'<h1>{course_desc["course_long"]}</h1>')

    # Show the project completion rate
    p.append('<h2>Project completion rates</h2>')
    p.append(make_project_completion_rates(accounts, course_desc))


    #############
    #   Forms   #
    #############

    # Vew scores form
    p.append('<h2>View scores</h2>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student:')
    p.append('</td><td>')
    p.append('<select name="scores">')
    p.append(f'<option value="entire_class">Entire class</option>')
    for name in sorted(accounts):
        p.append(f'<option value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="View scores">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Reset password form
    p.append('<h2>Reset a student\'s password</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post" onsubmit="hash_password(\'password\');">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student whose password to reset:')
    p.append('</td><td>')
    p.append('<select name="resetme">')
    p.append(f'<option value="">---</option>')
    for name in sorted(accounts):
        if (not 'ta' in accounts[name]) or accounts[name]['ta'] != 'true':
            p.append(f'<option value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Reset password!">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Add new students form
    p.append('<h2>Add new students</h3>')
    p.append('<p>The structure should be: last-name-comma-given-name(s). One name per line. No trailing punctuation.</p>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post"">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student names:')
    p.append('</td><td>')
    p.append('<textarea name="newstudents"></textarea>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Add new students">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Grant late tokens form
    p.append('<h2>Grant late tokens</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to grant tokens to:')
    p.append('</td><td>')
    p.append('<select name="student">')
    p.append(f'<option value="">---</option>')
    for name in sorted(accounts):
        p.append(f'<option value="{name}">{name} (has {accounts[name]["toks"]})</option>')
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

    # Set project score form
    p.append('<h2>Set project score</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to set score for:')
    p.append('</td><td>')
    p.append('<select name="student">')
    p.append(f'<option value="">---</option>')
    for name in sorted(accounts):
        p.append(f'<option value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('Project to set score for:')
    p.append('</td><td>')
    p.append('<select name="project">')
    p.append(f'<option value="">---</option>')
    for proj_id in course_desc['projects']:
        title = course_desc['projects'][proj_id]['title']
        p.append(f'<option value="{proj_id}">{title}</option>')
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

    # Impersonate form
    p.append('<h2>Impersonate</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student to impersonate:')
    p.append('</td><td>')
    p.append('<select name="impersonate">')
    p.append(f'<option value="">---</option>')
    for name in sorted(accounts):
        p.append(f'<option value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Impersonate">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Identify names form
    p.append('<h2>Identify names</h3>')
    p.append('<p>Paste a comma-separated list of student names below.')
    p.append('I will try to identify them and canonicalize them with my records.</p>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Student names:<br>(last-name, first-name)')
    p.append('</td><td>')
    p.append('<textarea name="student_names"></textarea>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Canonicalize">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Set multiple project scores form
    p.append('<h2>Set multiple project scores</h3>')
    p.append('<p>Names should be canonicalized.</p>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Project to set scores for:')
    p.append('</td><td>')
    p.append('<select name="project">')
    p.append(f'<option value="">---</option>')
    for proj_id in course_desc['projects']:
        title = course_desc['projects'][proj_id]['title']
        p.append(f'<option value="{proj_id}">{title}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td>')
    p.append('CSV data:<br>(last-name, first-name, score)<br>(one score per row)')
    p.append('</td><td>')
    p.append('<textarea name="set_scores"></textarea>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Set many scores">')
    p.append('</td></tr></table>')
    p.append('</form>')

    # Make TA form
    p.append('<h2>Make someone a TA</h3>')
    p.append(f'<form action="{dest_page}"')
    p.append(' method="post" onsubmit="hash_password(\'password\');">')
    p.append('<table>')
    p.append('<tr><td>')
    p.append('Name to make a TA:')
    p.append('</td><td>')
    p.append('<select name="maketa">')
    p.append(f'<option value="">---</option>')
    for name in sorted(accounts):
        if (not 'ta' in accounts[name]) or accounts[name]['ta'] != 'true':
            p.append(f'<option value="{name}">{name}</option>')
    p.append('</select>')
    p.append('</td></tr>')
    p.append('<tr><td></td><td><input type="submit" value="Grant TA authority">')
    p.append('</td></tr></table>')
    p.append('</form>')

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
    project_id:str,
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
    desc = course_desc['projects'][project_id]
    title = desc['title']
    due_time = desc['due_time']
    course_name = course_desc['course_long']

    p:List[str] = []
    page_start(p, session)

    if False:
        p.append('Sorry, submissions are no longer being accepted.<br><br>')
    else:
        p.append(f'<big><b>{course_name}</b></big><br>')
        p.append(f'<big>Submit <b>{title}</b></big><br>')

        # Tell the student if they have already received credit for this assignment.
        if project_id in account and account[project_id] > 0:
            p.append(f'(You have already received credit for {title}. Your score is {account[project_id]}<br><br>.')

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
def receive_submission(
        params: Mapping[str, Any],
        session: Session,
        course_desc:Mapping[str,Any],
        proj_id:str,
        accounts:Dict[str,Any],
        submit_page:str,
) -> Mapping[str,Any]:
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
    desc = course_desc['projects'][proj_id]
    days_late = max(0, int((((now_time - desc['due_time']).total_seconds() - submission_grace_seconds) // seconds_per_day) + 1))

    # Unpack the submission
    try:
        desc = course_desc['projects'][proj_id]
        title = desc['title']
        base_path, folder = unpack_submission(params, course_desc['course_short'], proj_id, session.name)
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        p:List[str] = []
        p.append('There was a problem with this submission:<br><br>')
        p.append(f'<font color="red">{str(e)}</font><br><br>')
        p.append('Please fix the issue and resubmit.')
        return {
            'succeeded': False,
            'page': {
                'results': ''.join(p),
            },
        }

    return {
        'succeeded': True,
        'account': account,
        'days_late': days_late,
        'base_path': base_path,
        'folder': folder,
        'proj_id': proj_id,
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

# This is called by AJAX POST from make_working_page.
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
def eval_thread(
        params: Mapping[str, Any], 
        session: Session, 
        eval_func:Callable[[Mapping[str,Any]],Mapping[str,Any]], 
        id:str,
        course_desc:Mapping[str,Any],
        proj_id: str,
        accounts:Dict[str,Any],
        submit_page:str, 
) -> None:
    # Find the job
    global jobs
    the_job = jobs[id]

    # Receive and unpack the submission
    submission = receive_submission(params, session, course_desc, proj_id, accounts, submit_page)
    if not ('succeeded' in submission) or not submission['succeeded']:
        the_job.results = cast(Mapping[str,Any], submission['page'])
        return

    # Evaluate the submission
    try:
        the_job.results = eval_func(submission)
    except RejectSubmission as rejection:
        p:List[str] = []
        p.append('Sorry, there was a problem with this submission:<br><br>')
        p.append(f'<font color="red">{str(rejection)}</font><br><br>')
        if len(rejection._args) > 0:
            p.append(f'Args passed in: <pre class="code">{" ".join(rejection._args)}</pre><br><br>')
        if len(rejection.input) > 0:
            p.append(f'Input fed in: <pre class="code">{rejection.input}</pre><br><br>')
        if len(rejection.output) > 0:
            p.append(f'Output: <pre class="code">{rejection.output}</pre><br><br>')
        p.append(rejection.extra)
        p.append('Please fix the issue and resubmit.')
        the_job.results = {
            'results': ''.join(p),
        }
    except BaseException as e:
        # Log the error
        random_id = make_random_id()
        print(f'An internal server error occurred! {random_id}', file=sys.stderr)
        if 'folder' in submission:
              print(f'  Folder={submission["folder"]}', file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

        # Generate some feedback
        p = []
        p.append(f'<font color="red">The submission server crashed while attempting to evaluate this submission. (This is probably an issue with the server rather than your code.) Please e-mail the instructor the following ID: {random_id} to help locate the relevant information for this crash in the server logs.</font><br><br>')
        the_job.results = {
            'results': ''.join(p),
        }

    # Save the feedback
    if 'folder' in submission:
        start_folder = submission['folder']
        with open(os.path.join(start_folder, '_feedback.txt'), 'w') as f:
            f.write(the_job.results['results'])


# Makes a job id
def make_random_id() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))

# Starts the evaluation thread and tells the user we are working on it
def launch_eval_thread(
        params: Mapping[str, Any], 
        session: Session, 
        course_desc:Mapping[str,Any],
        proj_id: str,
        accounts:Dict[str,Any],
        submit_page:str, 
) -> Mapping[str,Any]:
    global jobs
    purge_dead_jobs()

    # Get the account
    response = require_login(params, session, submit_page, accounts, course_desc)
    if 'content' in response:
        return response
    account = accounts[session.name]

    # Check whether this project has already been submitted
    desc = course_desc['projects'][proj_id]
    title = desc['title']
    if proj_id in account and account[proj_id] > 0 and (not 'ta' in account or account['ta'] != 'true'):
        submission = receive_submission(params, session, course_desc, proj_id, accounts, submit_page)
        score = account[proj_id]
        p:List[str] = []
        page_start(p, session)
        p.append(f'Thank you. Your resubmission of {title} has been received. Your score for this project remains {score}.')
        page_end(p)
        return {
            'content': ''.join(p),
        }

    # Make the job
    id = make_random_id()
    jobs[id] = Job()
    eval_func = course_desc['projects'][proj_id]['evaluator']
    thread = threading.Thread(target=eval_thread, args=(
        params, 
        session, 
        eval_func, 
        id, 
        course_desc, 
        proj_id, 
        accounts,
        submit_page,
    ))
    thread.start()
    return make_working_page(id, session)

# Generates functions that handle submitting and receiving project submissions
def page_maker_factory(
        proj_id:str, 
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
            proj_id,
            accounts,
            submit_page,
            receive_page,
        )
    def make_receive_page(params: Mapping[str, Any], session: Session) -> Mapping[str,Any]:
        return launch_eval_thread(
            params,
            session,
            course_desc,
            proj_id,
            accounts,
            submit_page,
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
