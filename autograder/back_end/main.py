from http_daemon import serve_pages, monitor_thread
import threading
import banana_quest
import pf2
import dsa
import autograder
import json
import os

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

    # Serve pages
    # delay_open_url(f'http://localhost:{port}/game.html', .1)
    serve_pages(config['port'], {
        'ajax.html': banana_quest.make_ajax_page,
        'game.html': banana_quest.make_game_page,
        'redirect.html': banana_quest.make_redirect_page,
        'log_out.html': autograder.make_log_out_page,
        'pf2_proj1_receive.html': pf2.pf2_proj1_receive,
        'pf2_proj1_submit.html': pf2.pf2_proj1_submit,
        'pf2_proj2_receive.html': pf2.pf2_proj2_receive,
        'pf2_proj2_submit.html': pf2.pf2_proj2_submit,
        'dsa_proj1_receive.html': dsa.dsa_proj1_receive,
        'dsa_proj1_submit.html': dsa.dsa_proj1_submit,
    })

if __name__ == "__main__":
    main()
