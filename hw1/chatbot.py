import socket, select, sys, termios, tty
import termios, requests, fcntl, os, locale
import re, random
from bs4 import BeautifulSoup as BS
from collections import defaultdict

schoolID = 'b05902052'
botID = 'bot_%s' % schoolID
roomName = '#CN_DEMO'

constellation_set = set([
    'Capricorn', 'Aquarius', 'Pisces', 
    'Aries', 'Taurus', 'Gemini', 
    'Cancer', 'Leo', 'Virgo', 'Libra', 
    'Scorpio', 'Sagittarius'
])

IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IRCSocket.connect(('127.0.0.1', 6667))

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
    # print(msgs)
    if len(msgs) >= 4:
        info, msg_class, receiver, *msg = msgs
        sender = info.split(':')[1].split('!')[0]
        if msg_class == 'PRIVMSG':
            if isinstance(msg, list):
                msg = ' '.join(msg).strip('\r\n')[1:]
            return sender, msg

    return None

def is_typing():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def nonblocking_readlines(f):
    """Generator which yields lines from F (a file object, used only for
       its fileno()) without blocking.  If there is no data, you get an
       endless stream of empty strings until there is data again (caller
       is expected to sleep for a while).
       Newlines are normalized to the Unix standard.
    """

    fd = f.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    enc = locale.getpreferredencoding(False)

    buf = bytearray()
    while True:
        try:
            block = os.read(fd, 8192)
        except BlockingIOError:
            yield ""
            continue

        if not block:
            if buf:
                yield buf.decode(enc)
                buf.clear()
            break

        buf.extend(block)

        while True:
            r = buf.find(b'\r')
            n = buf.find(b'\n')
            if r == -1 and n == -1: break

            if r == -1 or r > n:
                yield buf[:(n+1)].decode(enc)
                buf = buf[(n+1):]
            elif n == -1 or n > r:
                yield buf[:r].decode(enc) + '\n'
                if n == r+1:
                    buf = buf[(r+2):]
                else:
                    buf = buf[(r+1):]

received_stream = nonblocking_readlines(IRCSocket)
input_stream = nonblocking_readlines(sys.stdin)

def chatting(chatter):
    print('==========%s想跟你聯繫==========' % chatter)
    print('>', end=' ', flush=True)
    while True:
        received_msg = next(received_stream)
        if received_msg:
            result = parse(received_msg)
            if result is not None:
                sender, msg = result
                if sender == chatter:
                    print('\r%s : %s' % (chatter, msg))
                    print('>', end=' ', flush=True)
                    if msg.strip() == '!bye':
                        print('\r=========%s已離開聊天室=========' % chatter)
                        return

        input_msg = next(input_stream)
        if input_msg:
            send_privatemsg(chatter, input_msg.strip('\r\n'))
            print('>', end=' ', flush=True)

def get_bsObj(url):
    req = requests.get(url)
    bsObj = BS(req.text, features="lxml")
    return bsObj

def process(result):
    if result is None:
        return

    sender, command = result
    if not command:
        return

    bot_status = bot_statuses[sender]

    # general mode
    if not bot_status.mode:
        if command in constellation_set:
            send_privatemsg(sender, '今日運勢 水星逆行')
        elif command == '!guess':
            bot_status.mode = 'guess'
            send_privatemsg(sender, '猜一個1~10之間的數字！')
            bot_status.ans = random.randint(1, 10)
            bot_status.has_guessed = set()
        elif command == '!chat':
            chatting(sender)
        elif command.split()[0] == '!song':
            keyword = ' '.join(command.split()[1:]).strip()
            if not keyword:
                return
            queryURL = 'https://www.youtube.com/results?search_query=%s' % keyword
            bsObj = get_bsObj(queryURL)
            if not bsObj:
                send_privatemsg(sender, 'Due to the network issue, the function does not work now.')

            watchURL = bsObj.find('a', href=re.compile("^/watch\?v="))['href'].strip()
            send_privatemsg(sender, 'https://www.youtube.com' + watchURL)


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
                return
            elif bot_status.ans < command:
                hint = '小於%d!' % command
            else:
                hint = '大於%d!' % command

            if command in bot_status.has_guessed:
                hint = '你猜過%d了=_= %s' % (command, hint)
            else:
                bot_status.has_guessed.add(command)
            send_privatemsg(sender, hint)

send_msg('NICK %s' % (botID))
send_msg('USER %s' % (schoolID))
send_msg('JOIN %s' % (roomName))
send_msg("PRIVMSG %s : I'm %s " % (roomName, schoolID))

while True:
    while True:
        received_msg = next(received_stream)
        if not received_msg:
            continue
        print(received_msg.strip('\r\n'))
        process(parse(received_msg.strip('\r\n')))
