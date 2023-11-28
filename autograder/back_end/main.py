import os
from http_daemon import serve_pages, monitor_thread
import threading
import banana_quest
import pf2

def main() -> None:
    # Get set up
    os.chdir(os.path.join(os.path.dirname(__file__), '../front_end'))
    pf2.load_accounts()
    banana_quest.load_map()

    # Start the monitoring thread
    mt = threading.Thread(target=monitor_thread, args=(200,))
    mt.start()

    # Serve pages
    port = 8985
    # delay_open_url(f'http://localhost:{port}/game.html', .1)
    serve_pages(port, {
        'ajax.html': banana_quest.make_ajax_page,
        'game.html': banana_quest.make_game_page,
        'redirect.html': banana_quest.make_redirect_page,
        'pf2_proj1_receive.html': pf2.pf2_proj1_receive,
        'pf2_proj1_send.html': pf2.pf2_proj1_send,
        'pf2_log_out.html': pf2.log_out,
    })

if __name__ == "__main__":
    main()
