# ---------------------------------------------------------------
# The contents of this file are dedicated to the public domain as
# described at http://creativecommons.org/publicdomain/zero/1.0/.
# ---------------------------------------------------------------

from typing import Mapping, Any, Callable, Optional, Dict
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import webbrowser
import urllib.parse as urlparse
from http.cookies import SimpleCookie
import json
from datetime import datetime, timedelta
import sys
import os
import requests
import time
import traceback
import threading
import sd_notify
import random
import string
import tempfile

COOKIE_LEN = 12

def log(s:str) -> None:
    #print(f'{datetime.now()} {s}', file=sys.stderr)
    print(f'{datetime.utcnow()} {s}', file=sys.stderr)

    # # Find where a specific log message is coming from
    # if s.find('\n') >= 0:
    #     print('\n'.join(traceback.format_stack())) # print a stack trace with every log entry

def make_random_id(size:int) -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(size))

def new_session_id() -> str:
    now = datetime.now()
    date_str = f'{now.month:02}{now.day:02}{now.minute:02}'
    return date_str + make_random_id(COOKIE_LEN - len(date_str))

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

temp_folder = ''
page_maker: Callable[['Response',str,Mapping[str,Any],str,str],None]
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



class Response(BaseHTTPRequestHandler):
    def __init__(self, *args: Any) -> None:
        BaseHTTPRequestHandler.__init__(self, *args)

    def log_message(self, format:str, *args:Any) -> None:
        return

    def send_file(self, filename: str, content: bytes, session_id: str) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
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
        cookie = SimpleCookie(raw_cookie_text)
        if filename == 'ping.html':
            self.send_file(filename, b'pong', ping_sid) # special case for ping page
            return
        elif 'sid' in cookie:
            session_id = cookie['sid'].value
            # log(f'Got cookie: {cookie}')
            if len(session_id) != COOKIE_LEN:
                log(f'Bad session id {session_id}. Making new one.')
                session_id = new_session_id()
            if session_id == ping_sid:
                log(f'Using the ping session id {session_id}. Making new one.')
                session_id = new_session_id()
        else:
            session_id = new_session_id()
            log(f'No session id in "{cookie}". Making new one: {session_id}')

        # Generate the response
        global page_maker
        page_maker(self, filename, q, session_id, ip_address)

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
        brownie = SimpleCookie(brownie_str)
        if 'sid' in brownie:
            session_id = brownie['sid'].value
        else:
            cookie_str = self.headers.get('Cookie')
            cookie = SimpleCookie(cookie_str)
            if 'sid' in cookie:
                session_id = cookie['sid'].value
            else:
                raise ValueError('No cookie in POST.')
        if len(session_id) != COOKIE_LEN:
            log(f'Bad session id {session_id}. Making new one.')
            session_id = new_session_id()

        # Parse the content
        ct = self.headers.get('Content-Type') or ''
        upload_file_type = 'multipart/form-data'
        if ct[:len(upload_file_type)] == upload_file_type:
            params = self.parse_multipart_form()
        else:
            content_len = int(self.headers.get('Content-Length') or '')
            post_body = self.rfile.read(content_len)
            if len(post_body) > 0 and (post_body[0] == ord('{') or post_body[0] == ord('[')):
                params = json.loads(post_body)
            else:
                q = urlparse.parse_qs(post_body)
                q = { k.decode():(q[k][0] if len(q[k]) == 1 else q[k]).decode() for k in q } # type: ignore
                params = q # type: ignore

        # Generate the response
        global page_maker
        page_maker(self, filename, params, session_id, ip_address)

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
                        temp_form_folder = os.path.join(temp_folder, make_random_id(8))
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

# Use an inner server to abstract it away, and ensure my own methods don't override
# any critical operations used by the inner server.
class InnerServer(HTTPServer):
    # Let's overload the handle_error method to swallow ConnectionResetErrors
    def handle_error(self, request: Any, client_address: Any) -> None:
        ex_type, _, _ = sys.exc_info()
        if ex_type == ConnectionResetError:
            log('Connection reset')
        else:
            log('-'*40)
            log(f'Exception occurred during processing of request from {client_address}')
            traceback.print_exc()
            log('-'*40)



# Thread that pings the server at regular intervals and notifies systemd that it is still running.
# (This assumes this server is being run as a service in systemd with watchdog enabled.
# If that is not the case, this thread will just print a message to stderr and return.)
def monitor_thread(server:'WebServer', delay_seconds:float) -> None:
    notify = sd_notify.Notifier()
    if not notify.enabled():
        log('This server is not running as a service in systemd with watchdog enabled, so calling monitor does not make sense. Shutting down.')
        sys.exit(0)
    log('Starting monitoring thread')
    notify.ready()
    time.sleep(delay_seconds) # Give the server some time to initialize
    while server.keep_going:
        response = server.ping(30)
        if not server.keep_going: # Status may have changed while waiting for ping response
            break
        if response == 'pong':
            notify.notify() # healthy
        else:
            log(f'Failed health check: {response}. Stopping the server.')
            server.stop()
            notify.notify_error(response) # not healthy. The service manager will probably kill and restart this process
            break
        time.sleep(delay_seconds)
    log('Ending monitoring')


# Wraps Pythons Simple HTTP Server
class WebServer():
    def __init__(self,
            host: str = '127.0.0.1',
            port: int = 8080, 
            ssl_privkey: str = '',
            ssl_cert: str = '',
        ) -> None:
        self.host = host
        self.port = port
        print(f'port={port}')
        self.httpd = InnerServer(('', port), Response)

        # Make a cookie jar for ping
        self.ping_cookie_jar:Optional[requests.cookies.RequestsCookieJar] = None

        # Enable SSL
        if len(ssl_privkey) > 0 and len(ssl_cert) > 0:
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket, keyfile=ssl_privkey, certfile=ssl_cert, server_side=True)
            self.protocol = 'https://'
            log('Using SSL')
        else:
            self.protocol = 'http://'
            log('Not using SSL')

    # If successful, returns 'pong'.
    # If not, returns some other string describing the problem.
    # timeout is in seconds.
    def ping(self, timeout:int) -> str:
        try:
            r = requests.get(f'{self.protocol}{self.host}:{self.port}/ping.html', cookies=self.ping_cookie_jar, timeout=timeout)
            if 'Set-Cookie' in r.headers:
                self.ping_cookie_jar = r.cookies
            return r.text
        except:
            return traceback.format_exc()

    # Serve web pages until stop is called
    def serve(self, url_to_page: Callable[[Response,str,Mapping[str,Any],str,str],None]) -> None:
        global page_maker
        page_maker = url_to_page
        global temp_folder
        with tempfile.TemporaryDirectory() as td:
            temp_folder = td
            self.keep_going = True
            try:
                log(f'Serving on {self.host}:{self.port}')
                while self.keep_going:
                    self.httpd.handle_request() # blocks until a request comes in
            except KeyboardInterrupt:
                pass
        self.httpd.server_close()
        temp_folder = ''
        log(f'Server stopped')

    # Stops the server
    def stop(self) -> None:
        if self.keep_going:
            log(f'Starting to shut down')
            self.keep_going = False
            self.ping(1) # This unblocks "httpd.handle_request", so it will notice we want to shut down

    # Starts a thread that periodically pings the server to make sure it is still healthy
    def monitor(self, ping_gap:float) -> None:
        mt = threading.Thread(target=monitor_thread, args=(self, ping_gap))
        mt.start()


