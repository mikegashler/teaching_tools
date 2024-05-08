import os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

import banana_quest
import pf2
import dsa
import autograder
import json
from typing import Dict, Mapping, Any, Callable
import time
import sys
import signal
import traceback
import atexit

from session import Session, get_or_make_session, load_state, save_state
from http_daemon import log, WebServer, Response

web_server:WebServer

def exit_handler() -> None:
    web_server.stop()

def signal_handler(sig:int, frame) -> None: # type: ignore
    log(f'Got a SIGTERM')
    web_server.stop()
    time.sleep(0.5) # Give the server thread a moment to shut down
    sys.exit(0)

ajax_handlers:Dict[str,Callable[[Mapping[str,Any],Session],Mapping[str,Any]]] = {
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

def make_page(response:Response, url:str, params: Mapping[str, Any], session_id:str, ip_addr:str) -> None:
    # Try an ajax handler
    if url in ajax_handlers:
        sess = get_or_make_session(session_id, ip_addr)
        result = ajax_handlers[url](params, sess)
        response.send_response(200)
        if 'content' in result and len(result) == 1:
            response.send_header('Content-type', 'text/html')
            response.end_headers()
            response.wfile.write(bytes(result['content'], 'utf8'))
        else:
            response.send_header('Content-type', 'application/json')
            response.end_headers()
            response.wfile.write(bytes(json.dumps(result), 'utf8'))
        return

    # See if it is a client file
    client_filename = os.path.join('front_end', url)
    if os.path.exists(client_filename):
        with open(client_filename, 'rb') as f:
            content = f.read()
        response.send_file(url, content, session_id)
        return

    # Return a not found error
    response.send_response(404)
    response.send_header('Content-type', 'text/html')
    response.end_headers()
    response.send_file(url, (f'404 {url} not found.\n').encode(), session_id)

def main() -> None:
    config = {
        # 'host': 'hostname.com',
        'port': 80
        # 'monitor': 30,
        # 'ssl_privkey': '/path/to/privekey',
        # 'ssl_cert': '/path/to/ssl_cert'
    }
    if os.path.isfile('config.json'):
        print(f'loading config.json')
        with open('config.json', 'r') as f:
            s = f.read()
        config = json.loads(s)
    else:
        print(f'No config.json file in {os.getcwd()}. Using defaults.')
    host = str(config['host']) if 'host' in config else '127.0.0.1'
    port = int(config['port']) if 'port' in config else 8080
    ssl_privkey = str(config['ssl_privkey']) if 'ssl_privkey' in config else ''
    ssl_cert = str(config['ssl_cert']) if 'ssl_cert' in config else ''
    ping_gap = int(config['monitor']) if 'monitor' in config else 0

    # Get set up
    load_state()
    banana_quest.load_map()

    # Make a web server
    global web_server
    web_server = WebServer(host, port, ssl_privkey, ssl_cert)

    # Catch signals
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(exit_handler)

    # Set up monitoring
    # The ping_gap value specifies the delay (in seconds) between pings to check server health.
    # This value must be smaller than "WatchdogSec" in /etc/systemd/system/autograder.service
    if ping_gap > 0:
        web_server.monitor(ping_gap)
    else:
        print("Not monitoring (because 'monitor' was not specified in config.json)")

    # Generate submission and receive pages
    autograder.generate_submit_and_receive_pages(ajax_handlers, pf2.course_desc, pf2.accounts)
    autograder.generate_submit_and_receive_pages(ajax_handlers, dsa.course_desc, dsa.accounts)

    # Serve pages
    web_server.serve(make_page)

    # Save state
    save_state()

if __name__ == "__main__":
    main()
