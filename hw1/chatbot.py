import socket
from collections import defaultdict

IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IRCSocket.connect(('127.0.0.1', 6667))

schoolID = 'b05902052'
botID = 'bot_%s' % schoolID
roomName = '#CN_DEMO'

constellation_set = set([
    'Capricorn', 'Aquarius', 'Pisces', 
    'Aries', 'Taurus', 'Gemini', 
    'Cancer', 'Leo', 'Virgo', 'Libra', 
    'Scorpio', 'Sagittarius'
])

bot_status = defaultdict(str)

def send_msg(msg):
    IRCSocket.send(bytes(msg + '\r\n', encoding='utf-8'))

def send_privatemsg(receiver, msg):
    IRCSocket.send(bytes("PRIVMSG %s :%s \r\n" % (receiver, msg), encoding='utf-8'))

def parse(msg):
    msgs = msg.split(' ')
    print(msgs)
    if len(msgs) >= 4:
        info, msg_class, receiver, *msg = msgs
        sender = info.split(':')[1].split('!')[0]
        if msg_class == 'PRIVMSG':
            if isinstance(msg, list):
                msg = ' '.join(msg).strip()[1:]
            return sender, msg

    return None

def process(result):
    if result is None:
        return

    sender, command = result

    # general mode
    if not bot_status[sender]:
        if command in constellation_set:
            send_privatemsg(sender, 'Today is a lucky day.')
        elif command == '!guess':
            bot_status[sender] = 'guess'
            pass
    # guessing mode
    elif bot_status[sender] == 'guess':
        pass
    # chatting mode
    elif bot_status[sender] == 'chat':
        pass



send_msg('NICK %s' % (botID))
send_msg('USER %s' % (schoolID))
send_msg('JOIN %s' % (roomName))
send_msg("PRIVMSG %s : I'm %s " % (roomName, schoolID))

while True:
    IRCMsg = IRCSocket.recv(4096).decode()
    print(IRCMsg)
    process(parse(IRCMsg))
