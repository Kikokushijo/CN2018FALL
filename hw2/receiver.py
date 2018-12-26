from argparse import ArgumentParser
from collections import namedtuple
from sender import Header, Segment, header_type, segment_type, segment_size, unpack_segment
import queue
import struct
import socket

parser = ArgumentParser()
parser.add_argument('-f', '--filename', help='path of destination file')
parser.add_argument('-ri', '--recv_ip', default='127.0.0.1')
parser.add_argument('-rp', '--recv_port', default=8889, type=int)
parser.add_argument('-ai', '--agent_ip', default='127.0.0.1')
parser.add_argument('-ap', '--agent_port', default=8888, type=int)

def generate_ack_segment(ack_number, fin=0):
    header = struct.pack(header_type, *Header(0, 0, ack_number, fin, 0, 1))
    data = b''
    segment = struct.pack(segment_type, *Segment(header, data))
    return segment

def flush(file_reader, buffer):
    print('flush')
    while not buffer.empty():
        seg = buffer.get()
        file_reader.write(seg.data[:seg.head.length])

if __name__ == '__main__':

    args = parser.parse_args()
    filename = args.filename
    recv_ip = args.recv_ip
    recv_port = args.recv_port
    agent_ip = args.agent_ip
    agent_port = args.agent_port

    buffer_size = 32
    buffer = queue.Queue(maxsize=buffer_size)

    if args.filename is None:
        print(
            'Usage: python receiver.py -f <filename> -ri <receiver_ip> '
            '-rp <receiver_port> -ai <agent_ip> -ap <agent_port>'
            )
        quit()

    file_reader = open(filename, 'wb')

    receiver_address = (recv_ip, recv_port)
    agent_address = (agent_ip, agent_port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(receiver_address)

    received_seq_num = 0

    while True:

        segment = s.recv(segment_size)
        segment = unpack_segment(segment)

        if segment.head.fin:
            print('recv\tfin')
            ack_segment = generate_ack_segment(-1, fin=1)
            print('send\tfinack')
            s.sendto(ack_segment, agent_address)
            flush(file_reader, buffer)
            break

        if buffer.full():
            print('drop\tdata\t#%d' % (segment.head.seqNumber))
            ack_segment = generate_ack_segment(received_seq_num)
            print('send\tack\t#%d' % (received_seq_num))
            s.sendto(ack_segment, agent_address)
            flush(file_reader, buffer)

        elif segment.head.seqNumber == received_seq_num + 1:
            print('recv\tdata\t#%d' % (segment.head.seqNumber))
            ack_segment = generate_ack_segment(segment.head.seqNumber)
            print('send\tack\t#%d' % (segment.head.seqNumber))
            s.sendto(ack_segment, agent_address)
            buffer.put(segment)
            received_seq_num += 1
        else:
            print('drop\tdata\t#%d' % (segment.head.seqNumber))
            ack_segment = generate_ack_segment(received_seq_num)
            print('send\tack\t#%d' % (segment.head.seqNumber))
            s.sendto(ack_segment, agent_address)

    s.close()
    file_reader.close()