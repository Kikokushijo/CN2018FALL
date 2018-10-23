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

class BotStatus(object):
    def __init__(self):
        self.mode = ''

bot_statuses = defaultdict(BotStatus)

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

    bot_status = bot_statuses[sender]

    # general mode
    if not bot_status.mode:
        if command in constellation_set:
            send_privatemsg(sender, '今日運勢 水星逆行')
        elif command == '!guess':
            bot_status.mode = 'guess'
            send_privatemsg(sender, '猜一個1~10之間的數字！')
            bot_status.guess_ans = random.randint(1, 10)
        elif command == '!chat':
            bot_status.mode = 'chat'
        elif command == '!song':
            pass
    # guessing mode
    elif bot_status.mode == 'guess':
        try:
            command = int(command)
        except ValueError:
            pass
        else:
            if bot_status.ans == command:
                send_privatemsg(sender, '正確答案為%d! 恭喜猜中' % command)
                bot_statuses[sender] = BotStatus()
            elif bot_status.ans < command:
                hint = '小於%d!' % command
            else:
                hint = '大於%d!' % command

            if command in bot_status.has_guessed:
                hint = '你猜過%d了=_= %s' % (command, hint)
            else:
                bot_status.has_guessed.update(command)
            send_privatemsg(sender, hint)
    # chatting mode
    elif bot_status.mode == 'chat':
        if command == '!bye':
            bot_status.mode = ''
        else:
            pass



send_msg('NICK %s' % (botID))
send_msg('USER %s' % (schoolID))
send_msg('JOIN %s' % (roomName))
send_msg("PRIVMSG %s : I'm %s " % (roomName, schoolID))

while True:
    IRCMsg = IRCSocket.recv(4096).decode()
    print(IRCMsg)
    process(parse(IRCMsg))
