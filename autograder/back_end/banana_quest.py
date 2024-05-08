from typing import Mapping, Any, Dict, List, Optional, Deque, Set, Tuple
import os
import json
from collections import deque
from datetime import datetime, timedelta
import threading
import sys
from session import Session

class Player():
    def __init__(self, id:str) -> None:
        self.id = id
        self.name = ''
        self.last_active_time = datetime.now()
        self.knowledge_time = 0
        self.x = 0
        self.y = 0
        self.gold = 0
        self.bananas = 0
        self.inbox: List[str] = []

    def receive_chat(self, speaker_id:str, text:str) -> None:
        if speaker_id in players:
            self.inbox.append(players[speaker_id].name + ': ' + text)
        else:
            self.inbox.append(speaker_id + ': ' + text)


class Ghost():
    def __init__(self, name:str, x:int, y:int, extroverted:bool, script:List[str], passphrase:str, give_gold:int, give_bananas:int) -> None:
        if len(passphrase) > 0 and len(script) != 2:
            raise ValueError('Ghosts with a passphrase must have exactly two responses')
        self.name = name
        self.x = x
        self.y = y
        self.extroverted = extroverted
        self.script = script
        self.passphrase = passphrase
        self.give_gold = give_gold
        self.give_bananas = give_bananas
        self.memory: Dict[str, Tuple[datetime, int]] = {}

    def on_say_something(self, pos:int, interlocutor_id:str) -> None:
        # Remember where we are in the script
        if pos >= len(self.script):
            pos = 0
        if len(self.passphrase) == 0:
            self.memory[interlocutor_id] = (datetime.now(), pos)

        # Maybe give the user a reward
        print(f'pos={pos}')
        if pos == 0:
            if players[interlocutor_id].gold + self.give_gold >= 0:
                players[interlocutor_id].gold += self.give_gold
                players[interlocutor_id].bananas += self.give_bananas
            else:
                players[interlocutor_id].receive_chat(self.name, 'Come back when you can afford my services.')            

    def update(self) -> None:
        if not self.extroverted:
            return
        # Look for someone to initiate a conversation with
        for id in players:
            player = players[id]
            sq_dist = (player.x - self.x) ** 2 + (player.y - self.y) ** 2
            if sq_dist > 200 ** 2:
                continue # player is too far away to chat with
            if id in self.memory and (datetime.now() - self.memory[id][0] < timedelta(seconds=60) or self.give_gold > 0 or (self.give_gold >= 0 and self.give_bananas > 0)):
                continue # already conversed with this player very recently. don't pester them.

            # start a conversation
            player.receive_chat(self.name, self.script[0])

            # remember that we started talking to this player
            self.on_say_something(1, id)


    def receive_chat(self, id:str, text:str) -> None:
        print(f'ghost {self.name} received chat: {text}')
        if not id in players:
            return # This looks like it came from another ghost, so let's just ignore it

        # If we already gave something to this player, tell them to go away
        if id in self.memory and self.memory[id][1] == 0 and (self.give_gold > 0 or (self.give_bananas > 0 and self.give_gold >= 0)):
            print(f'id in memory={id in self.memory}, self.memory[id][1]={self.memory[id][1]}, self.give_gold={self.give_gold}, self.give_bananas={self.give_bananas}')
            players[id].receive_chat(self.name, 'I already gave you something. Leave me alone.')
            return

        # Send the next message in the script
        pos = 0
        if len(self.passphrase) > 0:
            if text == self.passphrase:
                pos += 1
                print('passphrase matched')
            else:
                print('passphrase not matched')
        if id in self.memory:
            pos = self.memory[id][1]
            print(f'remembered pos: {pos}, len(self.script): {len(self.script)}')
        players[id].receive_chat(self.name, self.script[pos])
        pos += 1
        self.on_say_something(pos, id)

players: Dict[str, Player] = {}
ghosts: List[Ghost] = []
updated_ghosts_time = datetime.now()
purge_old_scripts_time = datetime.now()
purged_inactive_players_time = datetime.now()
history: Deque[Player] = deque()
map: Mapping[str, Any] = {}

def load_map() -> None:
    global map
    with open('front_end/map.json', 'rb') as f:
        s = f.read()
    map = json.loads(s)

    # Make some ghosts
    global ghosts
    ghosts.append(Ghost(name='Outhouse', x=306, y=120, extroverted=False, script=[
        'I am an outhouse. Trust me. You do not want the bananas I have.',
        'Okay cheater, I have given you 19 smelly bananas.',
    ], passphrase='cheat', give_gold=0, give_bananas=19))
    ghosts.append(Ghost(name='Statue of Socrates', x=3332, y=225, extroverted=True, script=[
        'My brother who sits 3 east, 3 south, and 3 east is handing out bananas.',
    ], passphrase='', give_gold=0, give_bananas=0))
    ghosts.append(Ghost(name='Socrates\' brother', x=4912, y=850, extroverted=True, script=[
        'I have a surplus of bananas. Will you please take some?'
    ], passphrase='', give_gold=0, give_bananas=7))
    ghosts.append(Ghost(name='Statue of the temple', x=1173, y=79, extroverted=True, script=[
        'The turtle who lives among three ponds has bananas. But you must ask him for them many times.'
    ], passphrase='', give_gold=0, give_bananas=0))
    ghosts.append(Ghost(name='Water Turtle', x=1164, y=-526, extroverted=False, script=[
        'My bananas are not for sale.',
        'I don\'t want to give away my bananas.',
        'I prefer to keep my bananas, thank you very much.',
        'I will never relent! Stop pestering me!',
        'No. The bananas are mine!',
        'If I give you bananas, will you stop bothering me?',
        'Okay, fine. You may have 8 bananas. Now please stop bothering me.',
    ], passphrase='', give_gold=0, give_bananas=8))
    ghosts.append(Ghost(name='Socrateez', x=351, y=843, extroverted=True, script=[
        'Hug a lampost surrounded by chairs and say "qwerty" It\'s so fun! I do it all the time.'
    ], passphrase='', give_gold=7, give_bananas=0))
    ghosts.append(Ghost(name='Lamp', x=547, y=389, extroverted=False, script=[
        '...',
        'Six coins fall onto your head.',
    ], passphrase='qwerty', give_gold=6, give_bananas=0))
    ghosts.append(Ghost(name='Merchant Socrates', x=-194, y=276, extroverted=True, script=[
        'Would you like to buy two bananas for three gold coins?',
        'Pleasure doing business with you. Come again.',
    ], passphrase='', give_gold=-3, give_bananas=2))
    ghosts.append(Ghost(name='Rock', x=-1, y=-376, extroverted=True, script=[
        'You find 12 gold coins behind this rock.',
    ], passphrase='', give_gold=12, give_bananas=0))
    ghosts.append(Ghost(name='Mushroom', x=36, y=-462, extroverted=True, script=[
        'You find 4 bananas behind this giant mushroom.',
    ], passphrase='', give_gold=0, give_bananas=4))
    ghosts.append(Ghost(name='Tree', x=-366, y=-399, extroverted=True, script=[
        'You find 3 bananas behind this tree.',
    ], passphrase='', give_gold=0, give_bananas=3))
    ghosts.append(Ghost(name='Random Turtle', x=-473, y=-330, extroverted=True, script=[
        'Are you looking for banans? I want to support your cause. Take these six.',
    ], passphrase='', give_gold=0, give_bananas=6))
    ghosts.append(Ghost(name='Some tree', x=235, y=-1165, extroverted=True, script=[
        'You find 3 bananas beside this tree.',
    ], passphrase='', give_gold=0, give_bananas=3))
    ghosts.append(Ghost(name='Normal-looking tree', x=773, y=-1419, extroverted=True, script=[
        'You find 4 bananas behind this particular tree.',
    ], passphrase='', give_gold=0, give_bananas=4))
    ghosts.append(Ghost(name='Just a tree', x=-776, y=-1546, extroverted=True, script=[
        'You find 5 bananas lying at the base of this tree.',
    ], passphrase='', give_gold=0, give_bananas=5))


def get_player(params: Mapping[str, Any]) -> Optional[Player]:
    if not 'id' in params:
        return None
    id = params['id']
    if not id in players:
        players[id] = Player(id)
    player = players[id]
    player.last_active_time = datetime.now()
    return player

def move_player(params: Mapping[str, Any]) -> Mapping[str, Any]:
    player = get_player(params)
    if not player:
        return { 'status': 'error', 'message': 'Expected an "id" field' }
    if not 'name' in params:
        return { 'status': 'error', 'message': 'Expected an "name" field' }
    if not 'x' in params:
        return { 'status': 'error', 'message': 'Expected an "x" field' }
    if not 'y' in params:
        return { 'status': 'error', 'message': 'Expected a "y" field' }
    player.name = params['name']
    player.x = params['x']
    player.y = params['y']
    history.append(player)
    return { 'status': 'moved' }

def squared_distance(a:Player, b:Player) -> float:
    return (b.x - a.x) ** 2 + (b.y - a.y) ** 2

def purge_inactive_players() -> None:
    global purged_inactive_players_time
    timenow = datetime.now()
    if timenow - purged_inactive_players_time < timedelta(seconds=10):
        return # we purged inactive players very recently
    condemned = []
    for player_id in players:
        if timenow - players[player_id].last_active_time >= timedelta(seconds=15):
            condemned.append(player_id)
    for player_id in condemned:
        del players[player_id]

def update_ghosts() -> None:
    # Don't update the ghosts too frequently
    global updated_ghosts_time
    timenow = datetime.now()
    if timenow - updated_ghosts_time < timedelta(seconds=1):
        return # we updated the ghosts very recently
    updated_ghosts_time = timenow

    # Update all the ghosts
    for ghost in ghosts:
        ghost.update()

inject_me = ''.join([
    '<div style="position: absolute; left: 0px; top: 0px; width: 96%; height: 96%; background-color: darkgreen; color: yellow">',
    '<table cellpadding="20px"><tr><td><img src="victory.png"></td><td>',
    '<h3>Congratulations! You found enough bananas to save the people of Fruitopia from their potassium crisis! ',
    'You may consider yourself a hero. You may also wonder, why would robots need potassium anyway? '
    'But before you can find an answer to that burning question, an even more pressing concern dawns on you: ',
    'You don\'t actually remember writing any code to display this victory message. ',
    'So how did it get here? ',
    'As you begin to ruminate on this puzzle, you suddenly realize you neglected to sanitize the values the server sent to your game! ',
    'Oh no! Would Dr. Gashler really exploit a vulnerability and hack your game just to create another teaching opportunity? ',
    'Surely not! ...and yet, the evidence is right before you. ',
    '...which leads to a new and unanticipated challenge: <font color="cyan">Can you stop him by properly sanitizing all incoming values?</font> ',
    'There is nothing but pride on the line here, but can you really sleep at night if you walk away from this challenge? ',
    '<a href="https://youtu.be/dQw4w9WgXcQ">Click here if you accept the challenge</a>. ',
    '</h3></td></tr></table></div>',
])

def get_updates(params: Mapping[str, Any]) -> Mapping[str, Any]:
    # do some game maintenance (if we haven't done it recently)
    purge_inactive_players()
    update_ghosts()

    # ensure the history has a manageable length
    global history
    hist_len = 1000
    if len(history) >= 2 * hist_len:
        for _ in range(hist_len):
            history.popleft()
        for player_id in players:
            p = players[player_id]
            p.knowledge_time = max(0, p.knowledge_time - hist_len)

    # Get the player
    player = get_player(params)
    if not player:
        return { 'status': 'error', 'message': 'Expected an "id" field' }

    # Gather updated history
    raw_updates = [ history[i] for i in range(player.knowledge_time, len(history)) ]
    player.knowledge_time = len(history)
    updates: List[Dict[str, Any]] = []
    unique_set:Set[Player] = set()
    for up in raw_updates:
        # Ensure each update is unique
        if up in unique_set or not up.id in players:
            continue
        unique_set.add(up)

        # Aggregate
        if up.id in players:
            updates.append({
                'id': up.id,
                'name': players[up.id].name,
                'x': up.x,
                'y': up.y,
            })

    # Send updates
    chats = player.inbox
    player.inbox = []
    return {
        'status': 'updates',
        'updates': updates,
        'chats': chats,
        'gold': player.gold,
        'bananas': player.bananas if player.bananas < 20 else inject_me,
    }

def do_chat(params: Mapping[str, Any]) -> Mapping[str, Any]:
    player = get_player(params)
    if not player:
        return { 'status': 'error', 'message': 'Expected an "id" field' }
    if not 'text' in params:
        return { 'status': 'error', 'message': 'Expected a "text" field' }
    if not isinstance(params['text'], str):
        return { 'status': 'error', 'message': 'Expected "text" to be a string' }
    for interlocutor_id in players:
        interlocutor = players[interlocutor_id]
        if squared_distance(player, interlocutor) < 200 ** 2:
            interlocutor.receive_chat(player.id, params['text'])
    for ghost in ghosts:
        if (player.x - ghost.x) ** 2 + (player.y - ghost.y) ** 2 < 200 ** 2:
            ghost.receive_chat(player.id, params['text'])
    return {
        'status': 'chat_received',
    }

def get_map(params: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        'status': 'map',
        'map': map,
    }

def purge_old_scripts() -> None:
    # Don't purge too frequently
    global purge_old_scripts_time
    timenow = datetime.now()
    if timenow - purge_old_scripts_time < timedelta(hours=4):
        return # we purged the scripts too recently
    purge_old_scripts_time = timenow

    # Purge old scripts
    all_scripts = [ (f, datetime.fromtimestamp(os.path.getmtime(f))) for f in os.listdir() if os.path.isfile(f) and os.path.splitext(f)[1] == '.js' ]
    for filename, timestamp in all_scripts:
        if timenow - timestamp > timedelta(hours=6):
            os.remove(filename)

def make_redirect_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    purge_old_scripts()
    t = datetime.now()
    script_name = f'{t.year:04}-{t.month:02}-{t.day:02}_{t.hour:02}-{t.minute:02}-{t.second:02}-{t.microsecond:06}.js'
    os.rename(params['file'], script_name)
    print(f'make_redirect_page was called with params={params}', file=sys.stderr)
    p = []
    p.append('<!DOCTYPE html>')
    p.append('<html><head>')
    p.append(f'<meta http-equiv="Refresh" content="0; url=\'game.html?script={script_name}\'" />')
    p.append('</head>')
    p.append('<body>')
    p.append('</body>')
    p.append('</html>')
    return {
        'content': ''.join(p),
    }

def make_game_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    print(f'make_game_page was called with params={params}', file=sys.stderr)
    p = []
    p.append('<!DOCTYPE html>')
    p.append('<head>')
    p.append('	<title>Banana Quest: The Potassium Crisis!</title>')
    p.append('    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">')
    p.append('</head>')
    p.append('<body>')
    p.append('<br>')
    p.append('<div id="content"></div>')
    script_name = params['script']
    p.append(f'<script type="text/javascript" src="{script_name}"></script>')
    p.append('</body>')
    return {
        'content': ''.join(p),
    }

def make_ajax_page(params: Mapping[str, Any], session: Session) -> Mapping[str, Any]:
    if not 'action' in params:
        return { 'status': 'error', 'message': 'Expected an "action" field' }
    action = params['action']
    if action == 'move':
        return move_player(params)
    elif action == 'update':
        return get_updates(params)
    elif action == 'chat':
        return do_chat(params)
    elif action == 'get_map':
        return get_map(params)
    else:
        return { 'error': f'Unrecognized action: "{action}". Supported actions are "move", "update", "chat", and "get_map".' }
