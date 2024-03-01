from http_daemon import serve_pages, monitor_thread, Session
import threading
import banana_quest
import pf2
import dsa
import autograder
import json
import os
from typing import Dict, Callable, Mapping, Any

config = {
    'port': 80
}

if os.path.isfile('config.json'):
    print(f'loading config.json')
    with open('config.json', 'r') as f:
        s = f.read()
    config = json.loads(s)
else:
    print(f'no config.json file in {os.getcwd()}')

def main() -> None:
    # Get set up
    banana_quest.load_map()

    # Start the monitoring thread
    mt = threading.Thread(target=monitor_thread, args=(30,))
    mt.start()

    page_makers:Dict[str,Callable[[Mapping[str,Any],Session],Mapping[str,Any]]] = {
        'ajax.html': banana_quest.make_ajax_page,
        'game.html': banana_quest.make_game_page,
        'redirect.html': banana_quest.make_redirect_page,
        'log_out.html': autograder.make_log_out_page,
        'get_results.html': autograder.get_results,
        'pf2_view_scores.html': pf2.view_scores_page,
        'pf2_admin.html': pf2.admin_page,
        'dsa_view_scores.html': dsa.view_scores_page,
        'dsa_admin.html': dsa.admin_page,
    }
    autograder.generate_submit_and_receive_pages(page_makers, pf2.course_desc, pf2.accounts)
    autograder.generate_submit_and_receive_pages(page_makers, dsa.course_desc, dsa.accounts)

    # Serve pages
    # delay_open_url(f'http://localhost:{port}/game.html', .1)
    serve_pages(config['port'], page_makers)

if __name__ == "__main__":
    main()
