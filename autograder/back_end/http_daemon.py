# ---------------------------------------------------------------
# The contents of this file are dedicated to the public domain as
# described at http://creativecommons.org/publicdomain/zero/1.0/.
# ---------------------------------------------------------------

from typing import Mapping, Any, Callable, Optional, Dict, Tuple
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import webbrowser
import urllib.parse as urlparse
from http.cookies import SimpleCookie
import re
import json
from datetime import datetime, timedelta
import sys
import os
import requests
import time
import signal
import traceback
import threading
import sd_notify
import atexit
import random
import string
import tempfile

port = 0
COOKIE_LEN = 12


def make_random_id() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))

def log(s:str) -> None:
    print(f'{datetime.now()} {s}', file=sys.stderr)

def delay_open_url_helper(url: str, delay: float) -> None:
    time.sleep(delay)
    log(f'Opening {url}')
    webbrowser.open(url, new=2)

def delay_open_url(url: str, delay: float) -> None:
    t = threading.Thread(target=delay_open_url_helper, args=(url, delay))
    t.start()

mime_types = {
    '.svg': 'image/svg+xml',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.png': 'image/png',
    '.ico': 'image/png',
    '.js': 'text/javascript',
    '.zip': 'application/zip',
}

keep_going = True
temp_folder = ''
simpleWebServerPages: Mapping[str, Any] = {}
ping_sid = '000000000000'

# Finds prefix in line, and returns everything until the next double-quotes
def extract_named_string(line:str, prefix:str) -> str:
    beg = line.find(prefix)
    if beg >= 0:
        beg += len(prefix)
        end = line.find('"', beg)
    else:
        end = -1
    return line[beg:end]


class Session():
    def __init__(self) -> None:
        time_now = datetime.now()
        self.name = '' # The name of the account currently logged in with this session
        self.last_active_time = time_now
        self.last_ip = ''
        self.cookie = ''

    def logged_in(self) -> bool:
        log(f'logged in as {self.name}')
        return len(self.name) > 0

    def marshal(self) -> Mapping[str, Any]:
        return {
            'name': self.name,
            'date': self.last_active_time.isoformat(),
        }

    @staticmethod
    def unmarshal(ob: Mapping[str, Any]) -> 'Session':
        sess = Session()
        sess.name = ob['name']
        try:
            sess.last_active_time = datetime.fromisoformat(ob['date'])
        except ValueError:
            log(f'Error parsing date: {ob["date"] if "date" in ob else "no_date"}. Defaulting to now')
            sess.last_active_time = datetime.now()
        return sess

sessions: Dict[str, Session] = {}

# The first six digits are YYMMDD. The remaining digits are randomly drawn from alphanumerics
def new_session_id() -> str:
    now = datetime.now()
    date_str = f'{now.year - ((now.year // 100) * 100):02}{now.month:02}{now.day:02}'
    return date_str + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(COOKIE_LEN - len(date_str)))

def get_or_make_session(session_id:str, ip_address:str, http_method:str, cookie:str) -> Session:
    recognized = True
    if not session_id in sessions:
        sessions[session_id] = Session()
        recognized = False
    session = sessions[session_id]
    session.last_active_time = datetime.now()
    session.last_ip = ip_address
    session.cookie = cookie
    if not recognized:
        session.cookie += ' [not recognized]'
        log(f'Made a new session for id {session_id} in {http_method} request for cookie: {cookie}')
    return session

def unmarshal_state(ob: Mapping[str, Any]) -> None:
    global sessions
    ob_ses = ob['sessions']
    sessions = { ses_id: Session.unmarshal(ob_ses[ses_id]) for ses_id in ob_ses }

def marshal_state() -> Mapping[str, Any]:
    global sessions
    now_time = datetime.now()
    for session_id in sessions:
        if now_time - sessions[session_id].last_active_time >= timedelta(days=42):
            log(f'Dropping session {session_id} because it has not been used for 42 days. Now={now_time}, last_active_time={sessions[session_id].last_active_time}')
    return {
        'sessions': { session_id: sessions[session_id].marshal() for session_id in sessions if now_time - sessions[session_id].last_active_time < timedelta(days=42) },
    }

def save_state() -> None:
    with open('state.json', 'w') as f:
        f.write(json.dumps(marshal_state(), indent=1))
    log('state saved')

def load_state() -> None:
    global sessions
    if os.path.exists('state.json'):
        with open('state.json', 'r') as f:
            server_state = json.loads(f.read())
        log(f'state loaded')
    else:
        server_state = {
            'sessions': {},
        }
        log(f'no state.json file. Starting over from scratch')
    unmarshal_state(server_state)

class MyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args: Any) -> None:
        BaseHTTPRequestHandler.__init__(self, *args)

    def log_message(self, format:str, *args:Any) -> None:
        return

    def send_file(self, filename: str, content: str, session_id: str) -> None:
        self.send_response(200)
        #self.send_header("Access-Control-Allow-Origin", "*")
        name, ext = os.path.splitext(filename)
        if ext in mime_types:
            self.send_header('Content-type', mime_types[ext])
        else:
            self.send_header('Content-type', 'text/html')
        if ext == '.zip':
            self.send_header('Content-Disposition', 'attachment')
        expires = datetime.utcnow() + timedelta(days=720)
        s_expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        if session_id != ping_sid:
            self.send_header('Set-Cookie', f'sid={session_id}; samesite=strict; path=/; expires={s_expires}')
        self.end_headers()
        if isinstance(content, str):
            self.wfile.write(bytes(content, 'utf8'))
        else:
            try:
                self.wfile.write(content)
            except BaseException as e:
                log(f'Problem sending file: {filename}')
                raise e

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        #self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def do_GET(self) -> None:
        ip_address = self.client_address[0]

        # Parse url
        url_parts = urlparse.urlparse(self.path)
        filename = url_parts.path
        if filename[0] == '/':
            filename = filename[1:]
        if len(filename) == 0:
            filename = 'index.html'

        # Parse query
        q = urlparse.parse_qs(url_parts.query)
        q = { k:(q[k][0] if len(q[k]) == 1 else q[k]) for k in q } # type: ignore

        # Parse cookies
        raw_cookie_text = self.headers.get('Cookie')
        cookie:SimpleCookie[Any] = SimpleCookie(raw_cookie_text)
        if filename == 'ping.html':
            self.send_file(filename, 'pong', ping_sid) # special case for ping page
            return
        elif 'sid' in cookie:
            session_id = cookie['sid'].value
            cookie_str = session_id
            # log(f'Got cookie: {cookie}')
            if len(session_id) != COOKIE_LEN:
                log(f'Bad session id {session_id}. Making new one.')
                session_id = new_session_id()
                cookie_str += f' (invalid. making new one: {session_id})'
            if session_id == ping_sid:
                log(f'Using the ping session id {session_id}. Making new one.')
                session_id = new_session_id()
                cookie_str += f' (ping id? making new one: {session_id})'
        else:
            session_id = new_session_id()
            log(f'No session id in "{cookie}". Making new one: {session_id}')
            cookie_str = f'(none. making new one: {session_id})'

        # Get content
        if filename == 'ping.html':
            print('ping -> pong')
            self.send_file(filename, 'pong', ping_sid) # special case for ping page
            return
        elif filename in simpleWebServerPages:
            session = get_or_make_session(session_id, ip_address, 'GET', cookie_str)
            content = simpleWebServerPages[filename](q, session)['content']
        else:
            try:
                with open(filename, 'rb') as f:
                    content = f.read()
            except:
                log(f'current working directory: {os.getcwd()}')
                traceback.print_exc()
                content = f'404 {filename} not found.\n'
        self.send_file(filename, content, session_id)

    def do_POST(self) -> None:
        ip_address = self.client_address[0]

        # Parse url
        url_parts = urlparse.urlparse(self.path)
        filename = url_parts.path
        if filename[0] == '/':
            filename = filename[1:]

        # Parse cookies
        session_id = ''
        # The XHR specification forbids clients from setting 'Cookie',
        # so we work around that with 'Brownie' instead.
        brownie_str = self.headers.get('Brownie') or ''
        brownie:SimpleCookie[Any] = SimpleCookie(brownie_str)
        if 'sid' in brownie:
            session_id = brownie['sid'].value
        else:
            cookie_str = self.headers.get('Cookie')
            brownie_str = f'{cookie_str} (from cookie header?)'
            cookie:SimpleCookie[Any] = SimpleCookie(cookie_str)
            if 'sid' in cookie:
                session_id = cookie['sid'].value
            else:
                raise ValueError('No cookie in POST.')
        session = get_or_make_session(session_id, ip_address, 'POST', brownie_str)

        # Parse the content
        ct = self.headers.get('Content-Type') or ''
        upload_file_type = 'multipart/form-data'
        if ct[:len(upload_file_type)] == upload_file_type:
            params = self.parse_multipart_form()
        else:
            content_len = int(self.headers.get('Content-Length') or '')
            post_body = self.rfile.read(content_len)
            if content_len > 0 and (post_body[0] == 123 or post_body[0] == 91 or post_body[0] == 34): # 123='{', 91='[', 34='"' 
                params = json.loads(post_body)
            else:
                log(f'content_len={content_len}, post_body={str(post_body)}, path={self.path}')
                q = urlparse.parse_qs(post_body.decode())
                params = { k:(q[k][0] if len(q[k]) == 1 else q[k]) for k in q }

        # Generate a response
        if filename in simpleWebServerPages:
            response = simpleWebServerPages[filename](params, session)
            self.send_response(200)
            #self.send_header("Access-Control-Allow-Origin", "*")
            if 'content' in response and len(response.keys()) == 1:
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(response['content'], 'utf8'))
            else:
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), 'utf8'))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(f'{{"status":"error","message":"{filename} not found."}}', 'utf8'))

    # Returns the filename specified for the file
    def parse_multipart_form(self, max_size:int=16_000_000) -> Mapping[str, Any]:
        # Parse the multipart header
        content_type = self.headers['content-type']
        if not content_type:
            assert False, "No content-type header"
        boundary = content_type.split("=")[1].encode()
        # log(f'boundary={boundary}')
        remainbytes = int(self.headers['content-length'])
        # log(f'packet size={remainbytes}')
        assert remainbytes <= max_size, 'File too big'
        assert remainbytes > 0, 'Empty file packet'

        # Read each part of the multipart content
        temp_form_folder = ''
        form_data:Dict[str, Any] = {}
        line = b''
        while True:
            # Read the boundary
            if len(line) == 0:
                if remainbytes < 1:
                    break
                line = self.rfile.readline()
                remainbytes -= len(line)
                boundary_start = line.find(boundary)
                if boundary_start >= 0:
                    #print(f'ignoring {line[:boundary_start].decode()}')
                    line = line[boundary_start:]
            if not line.startswith(boundary):
                assert False, f"expected content ({line[:100].decode()}) to start with the boundary ({boundary[:100].decode()})"
            if line[len(boundary):].startswith(b'--'):
                break # Two dashes after the boundary indicates the end of the multi-part content

            # Read the Content-Disposition line
            line = self.rfile.readline()
            remainbytes -= len(line)
            line_str = line.decode()
            name = extract_named_string(line_str, 'name="')
            assert len(name) > 0, 'expected a name="value" pair to occur in the Content-Disposition line'
            filename = extract_named_string(line_str, 'filename="')

            # Skip any further headers (such as Content-Type) until we find the b'\r\n' that indicates the start of the content
            while True:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if len(line) == 0 or line == b'\r\n':
                    break

            # Read the content
            if len(filename) == 0:
                # Read the form value
                value = ''
                while remainbytes > 0:
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    boundary_start = line.find(boundary)
                    if boundary_start < 0:
                        value += line.decode()
                    else:
                        value += line[:boundary_start].decode()
                        line = line[boundary_start:]
                        break

                # Cut off the b'\r\n' at the end of the value
                if len(value) > 0 and value[-1] == '-':
                    value = value[:-1]
                if len(value) > 0 and value[-1] == '-':
                    value = value[:-1]
                if len(value) > 0 and value[-1] == '\n':
                    value = value[:-1]
                if len(value) > 0 and value[-1] == '\r':
                    value = value[:-1]
            else:
                if len(temp_form_folder) == 0:
                    while True:
                        temp_form_folder = os.path.join(temp_folder, make_random_id())
                        if not os.path.exists(temp_form_folder):
                            os.mkdir(temp_form_folder)
                            break

                # Read the file
                assert remainbytes > 0, 'Empty file'
                value = os.path.join(temp_form_folder, filename)
                with open(value, 'wb') as out:
                    while remainbytes > 0:
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        boundary_start = line.find(boundary)
                        if boundary_start < 0:
                            out.write(line)
                        else:
                            out.write(line[:boundary_start])
                            out.close()
                            line = line[boundary_start:]
                            break

            # Store the name-value pair in form_data
            form_data[name] = value
        return form_data

# Let's overload the handle_error method to swallow ConnectionResetErrors
class MyServer(HTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        ex_type, _, _ = sys.exc_info()
        if ex_type == ConnectionResetError:
            log('Connection reset')
        else:
            log('-'*40)
            log(f'Exception occurred during processing of request from {client_address}')
            traceback.print_exc()
            log('-'*40)

def serve_pages(the_port:int, pages:Mapping[str, Callable[[Mapping[str,Any], Session],Any]]) -> None:
    global port
    global temp_folder
    port = the_port
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(exit_handler)

    global simpleWebServerPages
    simpleWebServerPages = pages
    log(f'Serving on port {port}')
    httpd = MyServer(('', port), MyRequestHandler)

    load_state()
    with tempfile.TemporaryDirectory() as td:
        temp_folder = td
        global keep_going
        keep_going = True
        try:
            while keep_going:
                httpd.handle_request() # blocks until a request comes in
        except KeyboardInterrupt:
            pass
        httpd.server_close()
    save_state()
    log(f'http server stopped')

# If successful, returns 'pong'.
# If not, returns some other string describing the problem.
def ping(timeout:int) -> str:
    try:
        global port
        r = requests.get(f'http://localhost:{port}/ping.html', timeout=timeout)
        return r.text
    except:
        return traceback.format_exc()

# Saves state and joins all the threads
def graceful_shutdown() -> None:
    global keep_going
    if keep_going:
        keep_going = False
        ping(1) # This unblocks "httpd.handle_request", so it will notice we want to shut down
        log(f'Shutting down');
        time.sleep(0.3) # Give the http thread a moment to shut down

def signal_handler(sig:int, frame) -> None: # type: ignore
    log(f'Got a SIGTERM')
    graceful_shutdown()
    sys.exit(0)

def exit_handler() -> None:
    graceful_shutdown()

# Thread that pings the server at regular intervals and notifies systemd that it is still running.
# (This assumes this server is being run as a service in systemd with watchdog enabled.
# If that is not the case, this thread will just print a message to stderr and return.)
def monitor_thread(delay_seconds:float) -> None:
    notify = sd_notify.Notifier()
    if not notify.enabled():
        log('It looks like this server is not running as a service in systemd with watchdog enabled, so the monitor thread is just going to exit now.')
        return
    log('Starting monitoring thread')
    notify.ready()
    global keep_going
    time.sleep(delay_seconds) # Give the server some time to initialize
    while keep_going:
        response = ping(30)
        if not keep_going: # Status may have changed while waiting for ping response
            break
        if response == 'pong':
            notify.notify() # healthy
        else:
            log(f'Failed health check: {response}')
            graceful_shutdown()
            notify.notify_error(response) # not healthy. The service manager will probably kill and restart this process
        time.sleep(delay_seconds)
    log('Ending monitoring')


