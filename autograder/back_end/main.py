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
        'pf2_proj1_receive.html': pf2.pf2_proj1_receive,
        'pf2_proj2_receive.html': pf2.pf2_proj2_receive,
        'pf2_proj3_receive.html': pf2.pf2_proj3_receive,
        'pf2_proj4_receive.html': pf2.pf2_proj4_receive,
        'pf2_proj5_receive.html': pf2.pf2_proj5_receive,
        'pf2_proj6_receive.html': pf2.pf2_proj6_receive,
        'pf2_proj7_receive.html': pf2.pf2_proj7_receive,
        'pf2_proj8_receive.html': pf2.pf2_proj8_receive,
        'pf2_proj9_receive.html': pf2.pf2_proj9_receive,
        'pf2_proj10_receive.html': pf2.pf2_proj10_receive,
        'pf2_proj11_receive.html': pf2.pf2_proj11_receive,
        'pf2_proj12_receive.html': pf2.pf2_proj12_receive,
        'dsa_proj1_receive.html': dsa.dsa_proj1_receive,
        'dsa_proj2_receive.html': dsa.dsa_proj2_receive,
        'dsa_proj3_receive.html': dsa.dsa_proj3_receive,
        'dsa_proj4_receive.html': dsa.dsa_proj4_receive,
        'dsa_proj5_receive.html': dsa.dsa_proj5_receive,
        'dsa_proj6_receive.html': dsa.dsa_proj6_receive,
        'dsa_proj7_receive.html': dsa.dsa_proj7_receive,
        'dsa_proj8_receive.html': dsa.dsa_proj8_receive,
        'dsa_proj9_receive.html': dsa.dsa_proj9_receive,
        'dsa_proj10_receive.html': dsa.dsa_proj10_receive,
        'dsa_proj11_receive.html': dsa.dsa_proj11_receive,
        'dsa_proj12_receive.html': dsa.dsa_proj12_receive,
    }

    assert len(pf2.accounts) > 0, 'Looks like accounts have not yet loaded'
    autograder.generate_submit_pages(page_makers, pf2.course_desc, pf2.accounts)
    assert len(dsa.accounts) > 0, 'Looks like accounts have not yet loaded'
    autograder.generate_submit_pages(page_makers, dsa.course_desc, dsa.accounts)

    # Serve pages
    # delay_open_url(f'http://localhost:{port}/game.html', .1)
    serve_pages(config['port'], page_makers)

if __name__ == "__main__":
    main()
