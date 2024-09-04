from typing import Mapping, Any, List, Dict
from datetime import datetime
from http_daemon import log
from datetime import datetime
from threading import Lock
import autograder
import re
import os
from session import Session
import math

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

def submission_checks(submission:Mapping[str,Any]) -> None:
    # Check for forbidden files or folders
    forbidden_folders = [
        '.DS_Store',
        '.mypy_cache',
        '__pycache__',
        '.git',
        '.ipynb_checkpoints',
        '__MACOSX',
        '.settings',
        'backup',
        '.class',
    ]
    forbidden_extensions = [
        '', # usually compiled C++ apps
        '.bat', # windows batch files
        '.class', # compiled java
        '.dat',
        '.exe', 
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
    ]
    file_count = 0
    base_path = submission['base_path']
    for path, folders, files in os.walk(base_path):
        for forbidden_folder in forbidden_folders:
            if forbidden_folder in folders:
                raise autograder.RejectSubmission(f'Your zip file contains a forbidden folder: "{forbidden_folder}". (Note that the zip command adds to an existing zip file. To remove a file it is necessary to delete your zip file and make a fresh one.)', [], '', '')
        for filename in files:
            _, ext = os.path.splitext(filename)
            for forbidden_extension in forbidden_extensions:
                if ext == forbidden_extension:
                    raise autograder.RejectSubmission(f'Your zip contains an unnecessary file: "{filename}". Please submit only your code and your run.bash script.', [], '', '')
            if ext == '.zip' and path != base_path:
                raise autograder.RejectSubmission(f'Your zip contains other zip files. Please submit only your code and build script.  (Note that the zip command adds to an existing zip file. To remove a file it is necessary to delete your zip file and make a fresh one.)', [], '', '')
            if os.stat(os.path.join(path, filename)).st_size > 2000000:
                msg =f'The file {filename} is too big. All files must be less than 2MB.'
                log(msg)
                raise autograder.RejectSubmission(msg, [], '', '')
        file_count += len(files)

    # Check that there are not too many files
    max_files = 50
    if file_count > max_files:
        raise autograder.RejectSubmission(f'Your zip file contains {file_count} files! Only {max_files} are allowed.  (Note that the zip command adds to an existing zip file. To remove files it is necessary to delete your zip file and make a fresh one.)', [], '', '')

def basic_checks(args:List[str], input:str, output:str) -> None:
    # Check for errors
    if output.find('error:') >= 0:
        raise autograder.RejectSubmission(
            'There were errors.',
            args, input, output,
        )
    if output.find('Error:') >= 0:
        raise autograder.RejectSubmission(
            'There were errors.',
            args, input, output,
        )
    if output.find('Exception in thread') >= 0:
        raise autograder.RejectSubmission(
            'An exception was thrown.',
            args, input, output,
        )

def evaluate_map_editor(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1
    args:List[str] = []
    input = ''
    output = autograder.run_java_gui_submission(
        submission=submission,
        args=args,
        input=input,
        sandbox=False,
        update_code_to_inject = '''
            if (this.ag_frame_count == 2)
            {
                if (!this.ag_screen_cleared)
                    this.ag_terminate("In View.paintComponent, the screen should be cleared with the background color each frame before images are drawn.");
                AGSprite im = this.ag_find_sprite(0, 0);
                if (im == null)
                    this.ag_terminate("The currently selected image should be displayed in the top-left corner of the screen.");
                ag_first_selected_image = im.image;

                // Click to change the currently selected image
                this.ag_click(5, 5, 1);
            }
            else if (this.ag_frame_count == 4)
            {
                AGSprite im = this.ag_find_sprite(0, 0);
                if (im == null) {
                    this.ag_terminate("After clicking in the region of the currenly selected image, no selected image was displayed there anymore. An image should always be displayed there.");
                }
                ag_second_selected_image = im.image;
                if (ag_second_selected_image == ag_first_selected_image)
                {
                    this.ag_terminate("When the user clicks in the region of the currently selected image (in the top-left corner), it is supposed to change to the next image (and the former image should no longer be drawn).");
                }
            }
            else if (this.ag_frame_count == 6)
            {
                // Place an item on the map
                this.ag_click(500, 300, 1);
                ag_print_images();
            }
            else if (this.ag_frame_count == 8)
            {
                if (this.ag_sprites.size() < 2)
                {
                    this.ag_terminate("Clicking on the map should add an item to the map. (After clicking, the selected item was still the only image being drawn.)");
                }
                AGSprite recently_placed_item = this.ag_find_sprite(500, 300);
                if (recently_placed_item == null || recently_placed_item.image != ag_second_selected_image)
                    this.ag_terminate("When the user clicks on the map, it should place an item of the currently selected image, and each image should only be loaded once.");
                int target_x = 500 - recently_placed_item.image.getWidth(null) / 2;
                int target_y = 300 - recently_placed_item.image.getHeight(null);
                int sum_diff = Math.abs(target_x - recently_placed_item.x) + Math.abs(target_y - recently_placed_item.y);
                if (sum_diff > 20)
                {
                    ag_print_images();
                    ag_print_images();
                    this.ag_terminate("The image should be placed such that its bottom center is where the user clicked. Clicked at 500,300. Image width is " + Integer.toString(recently_placed_item.image.getWidth(null)) + ". Image height is " + Integer.toString(recently_placed_item.image.getHeight(null)) + ". Image drawn at " + Integer.toString(recently_placed_item.x) + "," + Integer.toString(recently_placed_item.y));
                }
            }
            else if (this.ag_frame_count >= 9 && this.ag_frame_count < 40)
            {
                // Cycle through all the images several times
                this.ag_click(15, 15, 1);
            }
            else if (this.ag_frame_count == 42)
            {
                ag_print_images();
                this.ag_click(50, 400, 1);
                this.ag_click(400, 50, 1);
                ag_print_images();
            }
            else if (this.ag_frame_count == 44)
            {
                if (this.ag_sprites.size() != 4) {
                    ag_print_images();
                    this.ag_terminate("Each click on the map (not including clicks on the currently selected image) should add one item to the map. After only 3 clicks on the map, there are " + Integer.toString(this.ag_sprites.size() - 1) + " map items (not including the currently selected image).");
                }
            }
            else if (this.ag_frame_count >= 100)
                this.ag_terminate("passed");
''',
    )
    basic_checks(args, input, output)
    try:
        with open(os.path.join(submission['folder'], 'ag_result.txt'), 'r') as f:
            result = f.read()
    except:
        raise autograder.RejectSubmission(
            'No results were generated.',
            args, input, output,
        )
    passed = 'passed'
    if result[:len(passed)] != passed:
        raise autograder.RejectSubmission(
            result,
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_objects(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1
    args:List[str] = []
    input = ''
    output = autograder.run_java_gui_submission(
        submission=submission,
        args=args,
        input=input,
        sandbox=False,
        member_variables_to_inject='''
    int scrolled_x;
    int scrolled_y;
''',
        update_code_to_inject = '''
            if (this.ag_frame_count == 2) {
                // Test that the screen was cleared, and click to change the current image
                if (!this.ag_screen_cleared)
                    this.ag_terminate("In View.paintComponent, the screen should be cleared with the background color each frame before images are drawn.");
                AGSprite im = this.ag_find_sprite(0, 0);
                if (im == null)
                    this.ag_terminate("The currently selected image should be displayed in the top-left corner of the screen.");
                ag_first_selected_image = im.image;

                // Click to change the currently selected image
                this.ag_click(5, 5, 1);
            } else if (this.ag_frame_count == 4) {
                // Test that the current image changed
                AGSprite im = this.ag_find_sprite(0, 0);
                if (im == null) {
                    this.ag_terminate("After clicking in the region of the currenly selected image, no selected image was displayed there anymore. An image should always be displayed there.");
                }
                ag_second_selected_image = im.image;
                if (ag_second_selected_image == ag_first_selected_image)
                {
                    this.ag_terminate("When the user clicks in the region of the currently selected image (in the top-left corner), it is supposed to change to the next image (and the former image should no longer be drawn).");
                }
            } else if (this.ag_frame_count == 6) {
                // Place an item on the map
                this.ag_click(500, 300, 1);
            } else if (this.ag_frame_count == 8) {
                // Test that an item was placed where the user clicked
                ag_print_images();
                if (this.ag_sprites.size() < 2)
                {
                    this.ag_terminate("Clicking on the map should add an item to the map. (After clicking, the selected item was still the only image being drawn.)");
                }
                AGSprite recently_placed_item = this.ag_find_sprite(500, 300);
                if (recently_placed_item == null || recently_placed_item.image != ag_second_selected_image)
                    this.ag_terminate("When the user clicks on the map, it should place an item of the currently selected image, and each image should only be loaded once.");
                int target_x = 500 - recently_placed_item.image.getWidth(null) / 2;
                int target_y = 300 - recently_placed_item.image.getHeight(null);
                int sum_diff = Math.abs(target_x - recently_placed_item.x) + Math.abs(target_y - recently_placed_item.y);
                if (sum_diff > 20)
                {
                    ag_print_images();
                    this.ag_terminate("The image should be placed such that its bottom center is where the user clicked. Clicked at 500,300. Image width is " + Integer.toString(recently_placed_item.image.getWidth(null)) + ". Image height is " + Integer.toString(recently_placed_item.image.getHeight(null)) + ". Image drawn at " + Integer.toString(recently_placed_item.x) + "," + Integer.toString(recently_placed_item.y));
                }
            } else if (this.ag_frame_count == 10) {
                // Start holding down the down arrow key
                this.ag_press_key(KeyEvent.VK_DOWN, 'd');
            } else if (this.ag_frame_count == 20) {
                // Release the down arrow key
                this.ag_release_key(KeyEvent.VK_DOWN, 'd');
            } else if (this.ag_frame_count == 22) {
                // Check that the item scrolled vertically
                AGSprite scrolled_item = this.ag_find_sprite(500, Integer.MAX_VALUE);
                scrolled_x = scrolled_item.bx();
                scrolled_y = scrolled_item.by();
                if (Math.abs(scrolled_x - 500) + 10 >= Math.abs(scrolled_y - 300))
                    this.ag_terminate("I placed an item on the map then pressed the down arrow for a while. I expected the map to scroll vertically, but that did not happen. (Did you put your scrolling code in Controller.keyPressed? If so, try moving that logic to Controller.update.)");
            } else if (this.ag_frame_count == 24) {
                // Click to place another item at (500,300)
                this.ag_click(500, 300, 1);
            } else if (this.ag_frame_count == 26) {
                // Check that the new item was placed correctly
                ag_print_images();
                AGSprite placed_after_scroll = this.ag_find_sprite(500, 300);
                if (Math.abs(placed_after_scroll.bx() - 500) + Math.abs(placed_after_scroll.by() - 300) > 10)
                    this.ag_terminate("I scrolled vertically, then clicked to place an item on the map. But the item was not placed where I clicked!");
            } else if (this.ag_frame_count == 28) {
                // Right-click to remove the new item
                ag_print_images();
                this.ag_click(500, 300, 3);
            } else if (this.ag_frame_count == 30) {
                // Make sure the scrolled item is the only remaining item
                ag_print_images();
                AGSprite scrolled_item = this.ag_find_sprite(500, Integer.MAX_VALUE);
                if (Math.abs(scrolled_item.bx() - scrolled_x) + Math.abs(scrolled_item.by() - scrolled_y) > 10)
                    this.ag_terminate("When I right-clicked, it removed an item that was not the closest item to where I clicked!");
            } else if (this.ag_frame_count >= 32 && this.ag_frame_count <= 38) {
                // Right-click (more times than there are images)
                this.ag_click(500, 300, 3);
            } else if (this.ag_frame_count == 40) {
                // Make sure there are no images remaining on the map
                ag_print_images();
                if (this.ag_sprites.size() > 1)
                    this.ag_terminate("I right-clicked many times, but it did not remove all the images.");
            } else if (this.ag_frame_count >= 42 && this.ag_frame_count < 48) {
                // Place six new items
                this.ag_click(10 * this.ag_frame_count, 300, 1);
            } else if (this.ag_frame_count >= 52 && this.ag_frame_count < 57) {
                // Remove five of them
                this.ag_click(430, 300, 3);
            } else if (this.ag_frame_count == 60) {
                // Make sure the remaining item is the one at (470,300)
                AGSprite remaining_item = this.ag_find_sprite(470, 300);
                if (Math.abs(remaining_item.bx() - 470) + Math.abs(remaining_item.by() - 300) > 6) {
                    ag_print_images();
                    this.ag_terminate("I placed six items on the map in a horizontal pattern, from left to right. Then, I right-clicked five times where the second item was placed. I expected the right-most item to be the only one remaining. But a different item remained.");
                }
            } else if (this.ag_frame_count == 62) {
                // Add an item at (400, 400)
                this.ag_click(400, 400, 1);
            } else if (this.ag_frame_count == 64) {
                // Save the map
                JButton save_button = this.ag_find_button(new String[]{"save", "write", "store", "backup", "record", "serialize", "marshal", "persist", "export", "to disk"});
                if (save_button == null)
                    this.ag_terminate("I could not find a button with the text 'save'");
                ag_print_images();
                save_button.push();
            } else if (this.ag_frame_count == 66) {
                // Add an item at (500, 500)
                this.ag_click(500, 500, 1);
            } else if (this.ag_frame_count == 68) {
                // Remove the item at (400, 400)
                this.ag_click(400, 400, 3);
            } else if (this.ag_frame_count == 70) {
                // Start holding down the down arrow key
                this.ag_press_key(KeyEvent.VK_DOWN, 'd');
            } else if (this.ag_frame_count == 76) {
                // Release the down arrow key
                this.ag_release_key(KeyEvent.VK_DOWN, 'd');
            } else if (this.ag_frame_count == 78) {
                // Load
                JButton load_button = this.ag_find_button(new String[]{"load", "read", "retrieve", "restore", "deserialize", "unmarshal", "import", "from"});
                if (load_button == null)
                    this.ag_terminate("I could not find a button with the text 'load'");
                load_button.push();
            } else if (this.ag_frame_count == 80) {
                // Make sure the images are where they were when we saved
                ag_print_images();
                AGSprite a = this.ag_find_sprite(470, Integer.MAX_VALUE);
                if (Math.abs(a.bx() - 470) < 6 && Math.abs(a.by() - 300) > 6) {
                    this.ag_print_images();
                    this.ag_terminate("I saved, then scrolled, then loaded. I expected the scroll position to be restored to the way it was when I saved, but this did not happen.");
                }
                if (Math.abs(a.bx() - 470) + Math.abs(a.by() - 300) > 6) {
                    this.ag_print_images();
                    this.ag_terminate("An item that was present when I saved disappeared as soon as I loaded");
                }
                AGSprite b = this.ag_find_sprite(400, 400);
                if (Math.abs(b.bx() - 400) + Math.abs(b.by() - 400) > 6) {
                    this.ag_print_images();
                    this.ag_terminate("I added an item, then saved, then deleted the item, then loaded. I expected that item to be restored, but it was not.");
                }
                AGSprite c = this.ag_find_sprite(500, 500);
                if (Math.abs(c.bx() - 500) + Math.abs(c.by() - 500) <= 20) {
                    this.ag_print_images();
                    this.ag_terminate("I saved, then added an item, then loaded, and the new item was still there! Loading should have gotten rid of it.");
                }
            } else if (this.ag_frame_count >= 82 && this.ag_frame_count < 88) {
                // Remove all items
                this.ag_click(400, 400, 3);
            } else if (this.ag_frame_count == 90) {
                // Add an item in the middle
                this.ag_click(300, 400, 1);
            } else if (this.ag_frame_count == 92) {
                // Add an item below
                this.ag_click(300, 500, 1);
            } else if (this.ag_frame_count == 94) {
                // Add an item above
                this.ag_click(300, 300, 1);
            } else if (this.ag_frame_count == 96) {
                // Check that the items are drawn in sorted order by y-value
                AGSprite a = this.ag_find_sprite(300, 300);
                AGSprite b = this.ag_find_sprite(300, 400);
                AGSprite c = this.ag_find_sprite(300, 500);
                int a_index = -1;
                int b_index = -1;
                int c_index = -1;
                for (int i = 0; i < this.ag_sprites.size(); i++) {
                    if (this.ag_sprites.get(i) == a)
                        a_index = i;
                    if (this.ag_sprites.get(i) == b)
                        b_index = i;
                    if (this.ag_sprites.get(i) == c)
                        c_index = i;
                }
                if (a_index < 0 || b_index < 0 || c_index < 0)
                    this.ag_terminate("An item disappeared after it was added to the map!");
                if (b_index <= a_index || c_index <= b_index)
                    this.ag_terminate("The items were not drawn in an order sorted by their y-value. Expected the items to be sorted by their y-value before drawing.");
            } else if (this.ag_frame_count >= 100)
                this.ag_terminate("passed");
''',
    )
    basic_checks(args, input, output)
    try:
        with open(os.path.join(submission['folder'], 'ag_result.txt'), 'r') as f:
            result = f.read()
    except:
        raise autograder.RejectSubmission(
            'No results were generated.',
            args, input, output,
        )
    passed = 'passed'
    if result[:len(passed)] != passed:
        raise autograder.RejectSubmission(
            result,
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_polymorphism(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)

    # Test 1
    args:List[str] = []
    input = ''
    output = autograder.run_java_gui_submission(
        submission=submission,
        args=args,
        input=input,
        sandbox=False,
        member_variables_to_inject='''
    ArrayList<Double> ag_xs;
    ArrayList<Double> ag_ys;
    ArrayList<Double> ag_ws;
    ArrayList<Double> ag_hs;
    int type_a;
    int type_b;
    int type_c;
    int type_d;

    static double ag_deviation(ArrayList<Double> arr) {
        double mean = 0.0;
        for (int i = 0; i < arr.size(); i++) {
            mean += arr.get(i).doubleValue();
        }
        mean /= arr.size();
        double var = 0.0;
        for (int i = 0; i < arr.size(); i++) {
            var += (arr.get(i).doubleValue() - mean) * (arr.get(i).doubleValue() - mean);
        }
        return Math.sqrt(var);
    }
''',
        initializers_to_inject='''
            this.ag_xs = new ArrayList<Double>();
            this.ag_ys = new ArrayList<Double>();
            this.ag_ws = new ArrayList<Double>();
            this.ag_hs = new ArrayList<Double>();
            this.type_a = 0;
            this.type_b = 0;
            this.type_c = 0;
            this.type_d = 0;
''',
        update_code_to_inject = '''
            int frames_per_item = 200;
            int step = this.ag_frame_count % frames_per_item;
            if (step == 1) {
                // Clear the arraylists
                this.ag_xs.clear();
                this.ag_ys.clear();
                this.ag_ws.clear();
                this.ag_hs.clear();

                // Add the item
                this.ag_click(300, 300, 1);
            } else if (step > 1 && step < 198) {
                // Measure image position and size
                AGSprite item = this.ag_find_sprite(300, 300);
                this.ag_xs.add(Double.valueOf(item.bx()));
                this.ag_ys.add(Double.valueOf(item.by()));
                this.ag_ws.add(Double.valueOf(item.w));
                this.ag_hs.add(Double.valueOf(item.h));
            } else if (step == 199) {
                // Compute deviations
                double xdev = ag_deviation(this.ag_xs);
                double ydev = ag_deviation(this.ag_ys);
                double wdev = ag_deviation(this.ag_ws);
                double hdev = ag_deviation(this.ag_hs);

                // Check results
                AGSprite current = this.ag_find_sprite(5, 5);
                int cur_wid = current.image.getWidth(null);
                String name = "";
                if (cur_wid == 120)
                    name = "chair";
                else if (cur_wid == 77)
                    name = "lamp";
                else if (cur_wid == 108)
                    name = "mushroom";
                else if (cur_wid == 164)
                    name = "outhouse";
                else if (cur_wid == 79)
                    name = "pillar";
                else if (cur_wid == 251)
                    name = "pond";
                else if (cur_wid == 147)
                    name = "rock";
                else if (cur_wid == 210)
                    name = "statue";
                else if (cur_wid == 242)
                    name = "tree";
                else if (cur_wid == 80)
                    name = "turtle";
                if (name.length() > 0) {
                    if (name.equals("chair") ||
                        name.equals("lamp") ||
                        name.equals("pond") ||
                        name.equals("rock") ||
                        name.equals("tree")) {
                        if (Math.abs(xdev) > 2 || Math.abs(ydev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to move");
                        if (Math.abs(wdev) > 2 || Math.abs(hdev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to change size");
                        this.type_a++;
                    } else if(name.equals("pillar") || name.equals("statue")) {
                        if (Math.abs(xdev) <= 2)
                            this.ag_terminate("The " + name + " is supposed to strafe back and forth horizontally");
                        if (Math.abs(ydev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to move vertically, just horizontally");
                        if (Math.abs(wdev) > 2 || Math.abs(hdev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to change size");
                        this.type_b++;
                    } else if (name.equals("outhouse") || name.equals("turtle")) {
                        if (Math.abs(xdev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to move horizontally. It is only supposed to jump vertically");
                        if (Math.abs(ydev) <= 2)
                            this.ag_terminate("The " + name + " is supposed to jump vertically at periodic intervals");
                        if (Math.abs(wdev) > 2 || Math.abs(hdev) > 2)
                            this.ag_terminate("The " + name + " is not supposed to change size");
                        this.type_c++;
                    } else if (name.equals("mushroom")) {
                        if (Math.abs(xdev) > 5 || Math.abs(ydev) > 5)
                            this.ag_terminate("The base (bottom-center) of the " + name + " is not supposed to move. The " + name + " is only supposed to change size");
                        if (Math.abs(wdev) <= 2 || Math.abs(hdev) <= 2)
                            this.ag_terminate("The mushroom is supposed to grow and shrink in an oscillating manner");
                        this.type_d++;
                    } else {
                        this.ag_terminate("Internal error with autograder 3429723");
                    }
                }    

                // Remove this item
                this.ag_click(300, 300, 3);

                // Change to next current item
                this.ag_click(5, 5, 1);

                if (this.type_a >= 4 && this.type_b >= 1 && this.type_c >= 1 && this.type_d >= 1)
                    this.ag_terminate("passed");
            } else if (this.ag_frame_count >= 10 * frames_per_item) {
                this.ag_terminate("Some of the expected images are not appearing. There should be a chair, lamp, mushroom, outhouse, pillar, pond, rock, statue, tree, and turtle. Or, if you changed the images, that might throw off the autograder's ability to detect them. Are you using the images that came with the starter kit?");
            }
''',
    )
    basic_checks(args, input, output)
    try:
        with open(os.path.join(submission['folder'], 'ag_result.txt'), 'r') as f:
            result = f.read()
    except:
        raise autograder.RejectSubmission(
            'No results were generated.',
            args, input, output,
        )
    passed = 'passed'
    if result[:len(passed)] != passed:
        raise autograder.RejectSubmission(
            result,
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def evaluate_ajax(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)
    args:List[str] = []
    input = ''
    output = autograder.run_nodejs_submission(
        submission=submission,
        args=args,
        input=input,
        sandbox=False,
        code_to_inject='''
const puppeteer = require('puppeteer');

const ag_sleep = async (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
};

async function ag_testit() {
    console.log('in testit');
    const browser = await puppeteer.launch()
    const page = await browser.newPage();
    page.on('console', message =>
        //console.log(`${message.type().substr(0, 3).toUpperCase()} ${message.text()}`)
        console.log(`${message.text()}`)
    ).on('pageerror', ({ message }) =>
        console.log(message)
    );/*.on('response', response =>
        console.log(`${response.status()} ${response.url()}`)
    ).on('requestfailed', request =>
        console.log(`${request.failure().errorText} ${request.url()}`)
    );*/

    // Navigate the page to a URL
    console.log(`[autograder] requesting http://${host}:${port}/client.html`)
    await page.goto(`http://${host}:${port}/client.html`);

    // Set screen size.
    //await page.setViewport({width: 1080, height: 1024});

    let max_pushes = 0;
    for(let i = 0; i < 13; i++) {
        // Push the button
        await page.evaluate(() => {
            let elements = document.getElementsByTagName('button');
            if (elements.length < 1)
                throw new Error('No buttons were found on this page!');
            for (let element of elements) {
                console.log(`[autograder] Clicking on button "${element.value}${element.innerHTML}"`);
                element.click();
            }
        });

        // Give the server some time to respond
        await ag_sleep(50);

        // See if the button-press was counted
        let pushes = await page.evaluate(() => {
            let how_many = document.getElementById('how_many');
            if (!how_many) {
                let spans = document.getElementsByTagName('span');
                if (spans.length < 1)
                    throw new Error('No <span> tags were found on this page! Expected one for displaying how many times the button was pushed');
                how_many = spans[0];
            }
            try {
                let pushes = Number(how_many.innerHTML);
                return pushes;
            } catch {
                console.log(`Expected the contents of the <span> tag to be a number. Got "${how_many.innerHTML}"`)
                return 0;
            }
        });
        max_pushes = Math.max(max_pushes, pushes);
    }

    // Check results
    if (max_pushes < 12)
        console.log('Error: I pushed the button 13 times. I expected to find a span containing a number that grew with each button press. But I could not find any such span.')

    // Shut down
    console.log('Shutting down browser...');
    await browser.close();
    console.log('Done. Passed.');
}

// Launch the autograder tests
ag_testit().then(() => { server.close(); });

'''
    )
    basic_checks(args, input, output)

    if output.find('12') < 0:
        raise autograder.RejectSubmission(
            'Failed to execute.',
            args, input, output,
        )

    # Accept the submission
    return accept_submission(submission)

def sq_dist(x1:float, y1:float, x2:float, y2:float) -> float:
    return (x2 - x1) ** 2 + (y2 - y1) ** 2

def evaluate_game(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)
    args:List[str] = []
    input = ''
    output = autograder.run_nodejs_submission(
        submission=submission,
        args=args,
        input=input,
        sandbox=False,
        code_to_inject='''
const puppeteer = require('puppeteer');

const ag_sleep = async (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
};

async function ag_testit() {
    const browser = await puppeteer.launch()

    // Make two browser pages    
    const page1 = await browser.newPage();
    const page2 = await browser.newPage();
    page1.on('console', message =>
        console.log(`${message.text()}`)
    ).on('pageerror', ({ message }) =>
        console.log(message)
    );
    page2.on('console', message =>
        console.log(`${message.text()}`)
    ).on('pageerror', ({ message }) =>
        console.log(message)
    );

    // Navigate the page to a URL
    console.log(`[autograder] requesting http://${host}:${port}/client.html`)
    await page1.goto(`http://${host}:${port}/client.html`);
    await page1.setViewport({width: 1080, height: 768});
    await page2.goto(`http://${host}:${port}/client.html`);
    await page2.setViewport({width: 1080, height: 768});

    // Give the page a little time to set up
    await ag_sleep(100);

    // Do some operations on page 1
    await page1.evaluate(async () => {
        let canvases = document.getElementsByTagName('canvas');
        if (canvases.length < 1) {
            console.log('[autograder] No canvas found. Evaluating the chat option.');

            // This looks like the chat option
            const _ag_sleep = async (ms) => {
                return new Promise(resolve => setTimeout(resolve, ms));
            };

            // Pass in a list and a starting element.
            // Fills the list with all text elements containing the specified text.
            const find_el_with_text = (text, results, el = document.body) => {
                if (el.nodeType === 3) { // text node
                    if (el.textContent && el.textContent.search(text) >= 0)
                        results.push(el);
                }
                for (node of el.childNodes) {
                    find_el_with_text(text, results, node);
                }
            };

            // Returns 'right', 'left', or null if it cannot determine
            const which_bubble = (el) => {
                if (!el) {
                    console.log('el is null');
                    return null;
                }
                if (el.classList && el.classList.contains('bubble_left'))
                    return 'left';
                if (el.classList && el.classList.contains('bubble_right'))
                    return 'right';
                return which_bubble(el.parentElement);
            };

            // Post an arbitrary word on page 1
            let textareas = document.getElementsByTagName('textarea');
            if (textareas.length < 1)
                throw new Error('No textareas were found on this page!');
            let arbitrary_word = 'serendipity';
            textareas[0].value = arbitrary_word;
            let buttons = document.getElementsByTagName('button');
            if (buttons.length < 1)
                throw new Error('No buttons were found on this page!');
            buttons[0].click();

            // Make sure it is posted immediately in an appropriate bubble
            await _ag_sleep(15);
            if (textareas[0].value.search(arbitrary_word) >= 0)
                throw new Error('After posting a message on page 1, the message still remained in the textarea where text is entered. It should be cleared from there.')
            let bubbles = [];
            find_el_with_text(arbitrary_word, bubbles);
            console.log(`bubbles.length=${bubbles.length}, bubbles[0]=${bubbles[0]}`);
            if (bubbles.length <= 0)
                throw new Error('I posted a message on page 1, but it was not displayed immediately. (Users should not have to wait for the server to respond to see their own messages.)');
            if (bubbles.length > 1)
                throw new Error('I posted a message on page 1, but it appeared multiple times on the screen. I expected it to appear in only one place.');
            let lr = which_bubble(bubbles[0]);
            if (lr === 'left')
                throw new Error('The messages you post are supposed to be displayed in a div with the class bubble_right. But I posted a message on page 1 and it was displayed in a div with the class bubble_left.');
            if (lr === 'right') {
            } else {
                console.log(`lr=${lr}`);
                throw new Error('The messages you post are supposed to be displayed in a div with the class bubble_right. But I posted a message on page 1 and the enclosing div did not have this class.');
            }
        } else {
            // This looks like the game option, so let's set up
            // a few operations to facilitate testing the game
            console.log('[autograder] Found a canvas. Evaluating the game option.');
            const canvas = canvases[0];

            CanvasRenderingContext2D.prototype.drawImage = (...args) => {
                if (args[0] && args[0].width)
                    console.log(`page 1 image at ${args[1] + args[0].width / 2},${args[2] + args[0].height}.`);
            };

            const left_click_on_canvas = (x, y) => {
                console.log(`p1 left-clicking at ${x}, ${y}`);
                const rect = canvas.getBoundingClientRect();
                const clickEvent = new MouseEvent('click', {
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    button: 0,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });
                canvas.dispatchEvent(clickEvent);
            }

            const right_click_on_canvas = (x, y) => {
                console.log(`p1 right-clicking at ${x}, ${y}`);
                const rect = canvas.getBoundingClientRect();
                const clickEvent = new MouseEvent('contextmenu', {
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    button: 2,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });
                //game.controller.onRightClick(clickEvent);
                canvas.dispatchEvent(clickEvent);
            }

            // Send the robot on page 1 to a destination
            left_click_on_canvas(55, 66);

            // Throw fireballs on page 1 to two different destinations
            right_click_on_canvas(777, 444);
            right_click_on_canvas(555, 111);
        }
    });

    // Give the server some time to propagate
    await ag_sleep(500);

    // Do some operations on page 2
    await page2.evaluate(async () => {
        let canvases = document.getElementsByTagName('canvas');
        if (canvases.length < 1) {
            // This looks like the chat option, so let's create some operations
            // for testing that.
            console.log('[autograder] No canvas found. Evaluating the chat option.');

            // Pass in a list and a starting element.
            // Fills the list with all text elements containing the specified text.
            const find_el_with_text = (text, results, el = document.body) => {
                if (el.nodeType === 3) { // text node
                    if (el.textContent && el.textContent.search(text) >= 0)
                        results.push(el);
                }
                for (node of el.childNodes) {
                    find_el_with_text(text, results, node);
                }
            };

            // Returns 'right', 'left', or null if it cannot determine
            const which_bubble = (el) => {
                if (!el) {
                    console.log('el is null');
                    return null;
                }
                if (el.classList && el.classList.contains('bubble_left'))
                    return 'left';
                if (el.classList && el.classList.contains('bubble_right'))
                    return 'right';
                return which_bubble(el.parentElement);
            };

            // Check that we received the arbitrary word
            let arbitrary_word = 'serendipity';
            let bubbles = [];
            find_el_with_text(arbitrary_word, bubbles);
            if (bubbles.length <= 0)
                throw new Error('I posted a message on page 1, then waited a while, but then could not find the message on page 2. Is chat even working?');
            if (bubbles.length > 1)
                throw new Error('I posted a message on page 1, but it appeared multiple times on page 2.');
            let lr = which_bubble(bubbles[0]);
            if (lr === 'right')
                throw new Error('The messages posed by someone else are supposed to be displayed in a div with the class bubble_left. But I posted a message from page 1 and it was displayed on page 2 in a div with the class bubble_right.');
            if (lr === 'left') {
            } else
                throw new Error('The messages others post are supposed to be displayed in a div with the class bubble_left. But I posted a message from page 1 and the enclosing div on page 2 did not have this class.');

            // Post an alternate word on page 2
            let alternate_word = 'extinguisher';
            let textareas = document.getElementsByTagName('textarea');
            if (textareas.length < 1)
                throw new Error('No textareas were found on this page!');
            textareas[0].value = alternate_word;
            let buttons = document.getElementsByTagName('button');
            if (buttons.length < 1)
                throw new Error('No buttons were found on this page!');
            buttons[0].click();

            // Check that the alternate word was posted immediately in an approprate bubble
            //await ag_sleep(15);
            if (textareas[0].value.search(alternate_word) >= 0)
                throw new Error('After posting a message on page 2, the message still remained in the textarea where text is entered. It should be cleared from there.')
            bubbles = [];
            find_el_with_text(alternate_word, bubbles);
            if (bubbles.length <= 0)
                throw new Error('I posted a message on page 2, but it was not displayed immediately. (Users should not have to wait for the server to respond to see their own messages.)');
            if (bubbles.length > 1)
                throw new Error('I posted a message on page 2, but it appeared multiple times on the screen. I expected it to appear in only one place.');
            lr = which_bubble(bubbles[0]);
            if (lr === 'left')
                throw new Error('The messages you post are supposed to be displayed in a div with the class bubble_right. But I posted a message on page 2 and it was displayed in a div with the class bubble_left.');
            if (lr === 'right') {
            } else
                throw new Error('The messages you post are supposed to be displayed in a div with the class bubble_right. But I posted a message on page 2 and the enclosing div did not have this class.');
        } else {
            // This looks like the game option, so let's set up
            // a few operations to facilitate testing the game
            console.log('[autograder] Found a canvas. Evaluating the game option.');
            const canvas = canvases[0];

            CanvasRenderingContext2D.prototype.drawImage = (...args) => {
                if (args[0] && args[0].width)
                    console.log(`page 2 image at ${args[1] + args[0].width / 2},${args[2] + args[0].height}.`);
            };

            const left_click_on_canvas = (x, y) => {
                console.log(`p2 left-clicking at ${x}, ${y}`);
                const rect = canvas.getBoundingClientRect();
                const clickEvent = new MouseEvent('click', {
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    button: 0,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });
                canvas.dispatchEvent(clickEvent);
            }

            const right_click_on_canvas = (x, y) => {
                console.log(`p2 right-clicking at ${x}, ${y}`);
                const rect = canvas.getBoundingClientRect();
                const clickEvent = new MouseEvent('contextmenu', {
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    button: 2,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });

                game.controller.onRightClick(clickEvent);
                canvas.dispatchEvent(clickEvent);
            }

            // Send the robot on page 2 to a destination
            left_click_on_canvas(555, 444);

            // Throw fireballs on page 2 to two different destinations
            right_click_on_canvas(777, 11);
            right_click_on_canvas(66, 333);
        }
    });

    // Give the server some time to propagate
    await ag_sleep(600);

    // Do some final operations on page 1
    const final_message = await page1.evaluate(async () => {
        let canvases = document.getElementsByTagName('canvas');
        if (canvases.length < 1) {
            // This looks like the chat option

            // Pass in a list and a starting element.
            // Fills the list with all text elements containing the specified text.
            const find_el_with_text = (text, results, el = document.body) => {
                if (el.nodeType === 3) { // text node
                    if (el.textContent && el.textContent.search(text) >= 0)
                        results.push(el);
                }
                for (node of el.childNodes) {
                    find_el_with_text(text, results, node);
                }
            };

            // Returns 'right', 'left', or null if it cannot determine
            const which_bubble = (el) => {
                if (!el) {
                    console.log('el is null');
                    return null;
                }
                if (el.classList && el.classList.contains('bubble_left'))
                    return 'left';
                if (el.classList && el.classList.contains('bubble_right'))
                    return 'right';
                return which_bubble(el.parentElement);
            };

            // Check that we received the alternate word
            let alternate_word = 'extinguisher';
            let bubbles = [];
            find_el_with_text(alternate_word, bubbles);
            if (bubbles.length <= 0)
                throw new Error('I posted a message on page 2, then waited a while, but then could find the message on page 1. Chat should work in both directions.');
            if (bubbles.length > 1)
                throw new Error('I posted a message on page 2, but it appeared multiple times on page 1.');
            let lr = which_bubble(bubbles[0]);
            if (lr === 'right')
                throw new Error('The messages posed by someone else are supposed to be displayed in a div with the class bubble_left. But I posted a message from page 2 and it was displayed on page 1 in a div with the class bubble_right.');
            if (lr === 'left') {
            } else
                throw new Error('The messages others post are supposed to be displayed in a div with the class bubble_left. But I posted a message from page 2 and the enclosing div on page 1 did not have this class.');
            return "Chat option passed all tests";
        } else {
            // There is nothing left that we need to do for the game option
            return "Game option";
        }
    });

    // Run for a few seconds
    await ag_sleep(4500);

    // Shut down
    console.log(`[autograder] ${final_message}`);
    console.log('Shutting down browser...');
    await browser.close();
}

// Launch the autograder tests
ag_testit().then(() => { server.close(); });

'''
    )
    basic_checks(args, input, output)

    if output.find('Game option') >= 0:
        #           p1robot p2robot  p1fb1   p1fb2   p2fb1   p2fb2
        spots_x = [ 55,     555,     777,    555,    777,    66 ]
        spots_y = [ 66,     444,     444,    111,    11,     333 ]
        min_sq_dists = [ 1e100 ] * 12

        # Evaluate all the image spots on page 1
        cur_pos = -1
        while True:
            sentinel_1 = 'page 1 image at '
            next_pos = output.find(sentinel_1, cur_pos + 1)
            if next_pos < 0:
                break
            cur_pos = next_pos
            sentinel_2_pos = output.find(',', cur_pos + len(sentinel_1))
            sentinel_3_pos = output.find('.', sentinel_2_pos + 1)
            if sentinel_3_pos > 0:
                x = float(output[cur_pos + len(sentinel_1):sentinel_2_pos])
                y = float(output[sentinel_2_pos + 1:sentinel_3_pos])
                for i in range(len(spots_x)):
                    dd = sq_dist(x, y, spots_x[i], spots_y[i])
                    min_sq_dists[i] = min(min_sq_dists[i], dd)

        # Evaluate all the image spots on page 2
        cur_pos = -1
        while True:
            sentinel_1 = 'page 2 image at '
            next_pos = output.find(sentinel_1, cur_pos + 1)
            if next_pos < 0:
                break
            cur_pos = next_pos
            sentinel_2_pos = output.find(',', cur_pos + len(sentinel_1))
            sentinel_3_pos = output.find('.', sentinel_2_pos + 1)
            if sentinel_3_pos > 0:
                x = float(output[cur_pos + len(sentinel_1):sentinel_2_pos])
                y = float(output[sentinel_2_pos + 1:sentinel_3_pos])
                for i in range(len(spots_x)):
                    dd = sq_dist(x, y, spots_x[i], spots_y[i])
                    min_sq_dists[6 + i] = min(min_sq_dists[6 + i], dd)

        # Check results
        min_dists = [ math.sqrt(x) for x in min_sq_dists ]
        for dist in min_dists:
            if dist > 150:
                raise autograder.RejectSubmission(
                    f'Some of the robots and/or fireballs did not go where they were directed to go from the other browser. (min_dists={min_dists})',
                    args, input, output,
                )

    # Accept the submission
    return accept_submission(submission)

def evaluate_async(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)
    if True:
        raise autograder.RejectSubmission(
            'Sorry, the autograder is not yet set up for this assignment.',
            [], '', '',
        )
    # Accept the submission
    return accept_submission(submission)

def evaluate_typescript(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)
    if True:
        raise autograder.RejectSubmission(
            'Sorry, the autograder is not yet set up for this assignment.',
            [], '', '',
        )
    # Accept the submission
    return accept_submission(submission)

def evaluate_python(submission:Mapping[str,Any]) -> Mapping[str, Any]:
    submission_checks(submission)
    if True:
        raise autograder.RejectSubmission(
            'Sorry, the autograder is not yet set up for this assignment.',
            [], '', '',
        )
    # Accept the submission
    return accept_submission(submission)

course_desc:Mapping[str,Any] = {
    'course_short': 'pp',
    'course_long': 'Programming Paradigms',
    'projects': {
        'map_editor': {
            'title': 'Project 1 - Map Editor',
            'due_time': datetime(year=2024, month=8, day=29, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_map_editor,
        },
        'objects': {
            'title': 'Project 2 - Objects',
            'due_time': datetime(year=2024, month=9, day=10, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_objects,
        },
        'polymorphism': {
            'title': 'Project 3 - Polymorphism',
            'due_time': datetime(year=2024, month=9, day=17, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_polymorphism,
        },
        'midterm1': {
            'title': 'Midterm 1',
            'due_time': datetime(year=2024, month=9, day=26, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 100,
        },
        'ajax': {
            'title': 'Project 4 - AJAX',
            'due_time': datetime(year=2024, month=10, day=3, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_ajax,
        },
        'game': {
            'title': 'Project 5 - Game or Chat',
            'due_time': datetime(year=2024, month=10, day=17, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_game,
        },
        'async': {
            'title': 'Project 6 - Async programming',
            'due_time': datetime(year=2024, month=10, day=29, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_async,
        },
        'midterm2': {
            'title': 'Midterm 2',
            'due_time': datetime(year=2024, month=10, day=31, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 100,
        },
        'async': {
            'title': 'Project 7 - Typescript',
            'due_time': datetime(year=2024, month=11, day=12, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_typescript,
        },
        'async': {
            'title': 'Project 8 - Python',
            'due_time': datetime(year=2024, month=11, day=26, hour=23, minute=59, second=59),
            'points': 100,
            'weight': 5,
            'evaluator': evaluate_python,
        },
        'final': {
            'title': 'Final exam',
            'due_time': datetime(year=2024, month=12, day=10, hour=23, minute=59, second=59),
            'weight': 20,
            'points': 100,
        },
    }
}

try:
    accounts:Dict[str,Any] = autograder.load_accounts(course_desc)
except:
    print(f'*** FAILED TO LOAD {course_desc["course_short"]} ACCOUNTS! Starting an empty file!!!')
    accounts = {}


accept_lock = Lock()

def accept_submission(submission:Mapping[str,Any]) -> Mapping[str,Any]:
    # Give the student credit
    with accept_lock:
        account = submission['account']
        days_late = submission['days_late']
        proj_id = submission['proj_id']
        covered_days = min(days_late, account["toks"])
        days_late -= covered_days
        score = max(30, 100 - 3 * days_late)
        if not (proj_id in account): # to protect from multiple simultaneous accepts
            log(f'Passed: title={proj_id}, days_late={days_late}, score={score}')
            account[proj_id] = score
            account["toks"] -= covered_days
            autograder.save_accounts(course_desc, accounts)

        # Make an acceptance page
        return autograder.accept_submission(submission, days_late, covered_days, score)

def view_scores_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.view_scores_page(params, session, f'{course_desc["course_short"]}_view_scores.html', accounts, course_desc)

def admin_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    return autograder.make_admin_page(params, session, f'{course_desc["course_short"]}_admin.html', accounts, course_desc)

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
        accounts:Dict[str,Any] = autograder.load_accounts(course_desc)
    except:
        accounts = {}
    autograder.save_accounts(course_desc, accounts)

if __name__ == "__main__":
    initialize_accounts()
