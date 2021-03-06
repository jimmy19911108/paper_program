'''
stun module
'''

import stun
import network_control as nc


class Stun():
    '''
    stun
    '''

    def __init__(self):

        full_cone = "Full Cone"  # 0
        restrict = "Restrict NAT"  # 1
        restrict_port = "Restrict Port NAT"  # 2
        symmetric = "Symmetric NAT"  # 3
        unknown = "Unknown NAT"  # 4
        self.nat_type = (full_cone, restrict, restrict_port, symmetric, unknown)

    def get_nat_type(self):
        '''
        get External NAT Type, IP and Port
        '''

        nat_type, external_ip, external_port = stun.get_ip_info(stun_host = nc.get_stun_server())

        print("\n\n=======================")
        print("NAT Type:", nat_type)
        print("External IP:", external_ip)
        print("External Port:", external_port)
        print("=======================\n\n")

        return nat_type, external_ip, external_port

    def check_nat_type(self):
        '''
        make a decision for the corresponding NAT type
        '''

        nat_type, external_ip, external_port = self.get_nat_type()

        if nat_type == self.nat_type[0]:
            print("LOG: Full Cone mode")
            return external_ip + ":" + str(external_port)
        elif nat_type in (self.nat_type[1], self.nat_type[2]):
            print("LOG: Restrict mode") #punching package
        else:
            print("LOG: Relay mode") #controller

"""import optparse
import struct
import sys
import time
from threading import Event, Thread

def bytes2addr(bytes):
    \"""Convert a hash to an address pair.\"""
    if len(bytes) != 8:
        raise ValueError("invalid bytes")
    host = socket.inet_ntoa(bytes[:4])
    port = struct.unpack("H", bytes[-4:-2])[
        0]  # unpack returns a tuple even if it contains exactly one item
    nat_type_id = struct.unpack("H", bytes[-2:])[0]
    target = (host, port)
    return target, nat_type_id


class Client():
    def __init__(self):
        try:
            master_ip = '127.0.0.1' if sys.argv[
                1] == 'localhost' else sys.argv[1]
            self.master = (master_ip, int(sys.argv[2]))
            self.pool = sys.argv[3].strip()
            self.sockfd = self.target = None
            self.periodic_running = False
            self.peer_nat_type = None
        except (IndexError, ValueError):
            print(sys.stderr, "usage: %s <host> <port> <pool>" % sys.argv[0])
            sys.exit(65)

    def request_for_connection(self, nat_type_id=0):
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockfd.sendto(self.pool + ' {0}'.format(nat_type_id), self.master)
        data, addr = self.sockfd.recvfrom(len(self.pool) + 3)
        if data != "ok " + self.pool:
            print(sys.stderr, "unable to request!")
            sys.exit(1)
        self.sockfd.sendto("ok", self.master)
        sys.stderr = sys.stdout
        print(sys.stderr,
              "request sent, waiting for partner in pool '%s'..." % self.pool)
        data, addr = self.sockfd.recvfrom(8)

        self.target, peer_nat_type_id = bytes2addr(data)
        print(self.target, peer_nat_type_id)
        self.peer_nat_type = NATTYPE[peer_nat_type_id]
        print(sys.stderr, "connected to {1}:{2}, its NAT type is {0}".format(
            self.peer_nat_type, *self.target))

    def recv_msg(self, sock, is_restrict=False, event=None):
        if is_restrict:
            while True:
                data, addr = sock.recvfrom(1024)
                if self.periodic_running:
                    print("periodic_send is alive")
                    self.periodic_running = False
                    event.set()
                    print("received msg from target,"
                          "periodic send cancelled, chat start.")
                if addr == self.target or addr == self.master:
                    sys.stdout.write(data)
                    if data == "punching...\n":
                        sock.sendto("end punching\n", addr)
        else:
            while True:
                data, addr = sock.recvfrom(1024)
                if addr == self.target or addr == self.master:
                    sys.stdout.write(data)
                    if data == "punching...\n":  # peer是restrict
                        sock.sendto("end punching", addr)

    def send_msg(self, sock):
        while True:
            data = sys.stdin.readline()
            sock.sendto(data, self.target)

    @staticmethod
    def start_working_threads(send, recv, event=None, *args, **kwargs):
        ts = Thread(target=send, args=args, kwargs=kwargs)
        ts.setDaemon(True)
        ts.start()
        if event:
            event.wait()
        tr = Thread(target=recv, args=args, kwargs=kwargs)
        tr.setDaemon(True)
        tr.start()

    def chat_fullcone(self):
        self.start_working_threads(self.send_msg, self.recv_msg, None,
                                   self.sockfd)

    def chat_restrict(self):
        from threading import Timer
        cancel_event = Event()

        def send(count):
            self.sockfd.sendto('punching...\n', self.target)
            print("UDP punching package {0} sent".format(count))
            if self.periodic_running:
                Timer(0.5, send, args=(count + 1, )).start()

        self.periodic_running = True
        send(0)
        kwargs = {'is_restrict': True, 'event': cancel_event}
        self.start_working_threads(self.send_msg, self.recv_msg, cancel_event,
                                   self.sockfd, **kwargs)

    def chat_symmetric(self):
        \"""
        Completely rely on relay server(TURN)
        \"""

        def send_msg_symm(sock):
            while True:
                data = 'msg ' + sys.stdin.readline()
                sock.sendto(data, self.master)

        def recv_msg_symm(sock):
            while True:
                data, addr = sock.recvfrom(1024)
                if addr == self.master:
                    sys.stdout.write(data)

        self.start_working_threads(send_msg_symm, recv_msg_symm, None,
                                   self.sockfd)

    def main(self, test_nat_type=None):
        \"""
        nat_type是自己的nat类型
        peer_nat_type是从服务器获取的对方的nat类型
        选择哪种chat模式是根据nat_type来选择, 例如我这边的NAT设备是restrict, 那么我必须得一直向对方发包,
        我的NAT设备才能识别对方为"我已经发过包的地址". 直到收到对方的包, periodic发送停止
        \"""
        if not test_nat_type:
            nat_type, _, _ = self.get_nat_type()
        else:
            nat_type = test_nat_type  # 假装正在测试某种类型的NAT
        try:
            self.request_for_connection(nat_type_id=NATTYPE.index(nat_type))
        except ValueError:
            print("NAT type is %s" % nat_type)
            self.request_for_connection(nat_type_id=4)  # Unknown NAT

        if nat_type == UnknownNAT or self.peer_nat_type == UnknownNAT:
            print("Symmetric chat mode")
            self.chat_symmetric()
        if nat_type == SymmetricNAT or self.peer_nat_type == SymmetricNAT:
            print("Symmetric chat mode")
            self.chat_symmetric()
        elif nat_type == FullCone:
            print("FullCone chat mode")
            self.chat_fullcone()
        elif nat_type in (RestrictNAT, RestrictPortNAT):
            print("Restrict chat mode")
            self.chat_restrict()
        else:
            print("NAT type wrong!")

        while True:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                print("exit")
                sys.exit(0)
"""