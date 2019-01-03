from argparse import ArgumentParser
from collections import namedtuple
import queue
import struct
import socket
import fcntl
import time
import os
import errno

parser = ArgumentParser()
parser.add_argument('-f', '--filename', help='path of source file')
parser.add_argument('-si', '--send_ip', default='127.0.0.1')
parser.add_argument('-sp', '--send_port', default=8887, type=int)
parser.add_argument('-ai', '--agent_ip', default='127.0.0.1')
parser.add_argument('-ap', '--agent_port', default=8888, type=int)

Header = namedtuple('Header', ['length', 'seqNumber', 'ackNumber', 'fin', 'syn', 'ack'])
Segment = namedtuple('Segment', ['head', 'data'])

data_size = 1000
header_type = '6i'
segment_type = '%ds%ds' % (struct.calcsize(header_type), data_size)
segment_size = struct.calcsize(segment_type)

def generate_segment(length, seqNumber, ackNumber, fin, syn, ack, data):
    header = struct.pack(header_type, *Header(length, seqNumber, ackNumber, fin, syn, ack))
    segment = struct.pack(segment_type, *Segment(header, data))
    return segment

def unpack_segment(segment):
    header, data = struct.unpack(segment_type, segment)
    header = Header(*struct.unpack(header_type, header))
    return Segment(header, data)

if __name__ == '__main__':

    args = parser.parse_args()
    filename = args.filename
    send_ip = args.send_ip
    send_port = args.send_port
    agent_ip = args.agent_ip
    agent_port = args.agent_port

    if args.filename is None:
        print(
            'Usage: python sender.py -f <filename> -si <sender_ip> '
            '-sp <sender_port> -ai <agent_ip> -ap <agent_port>'
            )
        quit()

    file_reader = open(filename, 'rb')
    buffer = queue.Queue()

    sender_address = (send_ip, send_port)
    agent_address = (agent_ip, agent_port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(sender_address)
    fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)

    is_EOF = False
    window_size = 1
    threshold = 16
    fetched_seq_num = 0
    prev_fetched_seq_num = 0
    acked_seq_num = 0
    resend_timeout = 1.0

    while not is_EOF or not buffer.empty():

        while not is_EOF and buffer.qsize() < window_size:
            msg = file_reader.read(data_size)
            if msg:
                fetched_seq_num += 1
                segment = generate_segment(len(msg), fetched_seq_num, 0, 0, 0, 0, msg)
                buffer.put(segment)
            else:
                is_EOF = True
                # segment = generate_segment(len(msg), 0, 0, 1, 0, 0, msg)
            # buffer.put(segment)
        
        for i in range(min(window_size, buffer.qsize())):
            seg = buffer.queue[i]
            reconstruct_seg = unpack_segment(seg)
            prefix = 'send' if reconstruct_seg.head.seqNumber > prev_fetched_seq_num else 'resnd'
            assert not reconstruct_seg.head.fin
            print('%s\tdata\t#%d,\twinSize = %d' % (prefix, reconstruct_seg.head.seqNumber, window_size))
            s.sendto(seg, agent_address)
        prev_fetched_seq_num = fetched_seq_num
        time.sleep(resend_timeout)

        while True:
            try:
                segment = s.recv(segment_size)
                segment = unpack_segment(segment)
                assert segment.head.ack and not segment.head.fin
                print('recv\tack\t#%d' % segment.head.ackNumber)
                acked_seq_num = max(acked_seq_num, segment.head.ackNumber)
            except socket.error as error:
                if error.errno == errno.EAGAIN or error.errno == errno.EWOULDBLOCK:
                    break
                else:
                    print('Another error occurs.')
                    quit()
        
        if acked_seq_num == fetched_seq_num:
            if window_size < threshold:
                window_size *= 2
            else:
                window_size += 1
        else:
            threshold = max(window_size // 2, 1)
            window_size = 1
            print('time\tout,\t\tthreshold = %d' % (threshold))

        while (not buffer.empty()) and unpack_segment(buffer.queue[0]).head.seqNumber <= acked_seq_num:
            _ = buffer.get()

    resnd_fin = False
    while True:
        segment = generate_segment(len(msg), 0, 0, 1, 0, 0, msg)
        print('resnd\tfin' if resnd_fin else 'send\tfin')
        s.sendto(segment, agent_address)
        time.sleep(resend_timeout)
        try:
            segment = s.recv(segment_size)
            segment = unpack_segment(segment)
            assert segment.head.ack and segment.head.fin
            if segment.head.fin:
                print('recv\tfinack')
                quit()
        except socket.error as error:
            if error.errno == errno.EAGAIN or error.errno == errno.EWOULDBLOCK:
                break
            else:
                print('Another error occurs.')
                quit()

    s.close()
    file_reader.close()