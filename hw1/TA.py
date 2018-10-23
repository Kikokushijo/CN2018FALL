import socket
import random
import time

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

def send_privatemsg(msg, receiver):
    IRCSocket.send(bytes("PRIVMSG %s :%s \r\n" % (receiver, msg), encoding='utf-8'))

send_msg('NICK %s' % (TAID))
send_msg('USER %s' % (TAID))
send_msg('JOIN %s' % (roomName))
send_msg("PRIVMSG %s :I'm %s " % (roomName, TAID))

while True:
    # IRCMsg = IRCSocket.recv(4096).decode()
    # print(IRCMsg)
    send_privatemsg(random.sample(constellation_set, k=1)[0], botID)
    time.sleep(3)
