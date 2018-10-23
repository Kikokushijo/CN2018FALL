import socket
import random
import time, sys, fcntl, os, locale

IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IRCSocket.connect(('127.0.0.1', 6667))

schoolID = 'b05902052'
botID = 'bot_%s' % schoolID
TAID = 'TA1'
roomName = '#CN_DEMO'

constellation_set = set([
    'Capricorn', 'Aquarius', 'Pisces', 
    'Aries', 'Taurus', 'Gemini', 
    'Cancer', 'Leo', 'Virgo', 'Libra', 
    'Scorpio', 'Sagittarius'
])

def send_msg(msg):
    IRCSocket.send(bytes(msg + '\r\n', encoding='utf-8'))

def send_privatemsg(receiver, msg):
    IRCSocket.send(bytes("PRIVMSG %s :%s \r\n" % (receiver, msg), encoding='utf-8'))

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

send_msg('NICK %s' % (TAID))
send_msg('USER %s' % (TAID))
send_msg('JOIN %s' % (roomName))
send_msg("PRIVMSG %s :I'm %s " % (roomName, TAID))

def test_constellation():
    send_privatemsg(botID, random.sample(constellation_set, k=1)[0])

received_stream = nonblocking_readlines(IRCSocket)
input_stream = nonblocking_readlines(sys.stdin)
while True:

    while True:
        received_msg = next(received_stream)
        if not received_msg:
            break
        print(received_msg.strip())

    while True:
        sent_msg = next(input_stream)
        if not sent_msg:
            break
        send_privatemsg(botID, sent_msg.strip())