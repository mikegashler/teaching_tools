from datetime import datetime, timedelta
from typing import Mapping, Any, Dict
import random
import string
import json
import os

from http_daemon import log

COOKIE_LEN = 12
last_save_sessions_time = datetime.now()

class Session():
    def __init__(self) -> None:
        time_now = datetime.now()
        self.name = '' # The name of the account currently logged in with this session
        self.last_active_time = time_now
        self.last_ip = ''

    def logged_in(self) -> bool:
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

def get_or_make_session(session_id:str, ip_address:str) -> Session:
    recognized = True
    if not session_id in sessions:
        sessions[session_id] = Session()
        recognized = False
    session = sessions[session_id]
    session.last_active_time = datetime.now()
    session.last_ip = ip_address
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

def save_sessions() -> None:
    with open('state.json', 'w') as f:
        f.write(json.dumps(marshal_state(), indent=1))
    log('state saved')

def load_state() -> None:
    global sessions
    global last_save_sessions_time
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
    last_save_sessions_time = datetime.now()

def maybe_save_sessions() -> None:
    global last_save_sessions_time
    now_time = datetime.now()
    if now_time - last_save_sessions_time > timedelta(minutes=15):
        last_save_sessions_time = now_time
        save_sessions()
