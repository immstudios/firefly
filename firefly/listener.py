import json
import socket
import time
import requests

from .common import *

__all__ = ["SeismicListener"]

def readlines(f):
    buff = b""
    for ch in f.iter_content(1):
        ch = ch
        if ch == b"\n":
            yield buff.decode("ascii")
            buff = b""
        else:
            buff += ch
    yield buff.decode("ascii")


class SeismicMessage(object):
    def __init__(self, packet):
        self.timestamp, self.site_name, self.host, self.method, self.data = packet


class SeismicListener(QThread):
    def __init__(self, site_name, addr, port):
        QThread.__init__(self, None)
        self.site_name = site_name

        self.should_run = True
        self.halted = False
        self.last_msg = time.time()
        self.queue = []

        self.addr = addr
        self.port = port
        self.start()


    def run(self):
        logging.info("Starting Seismic listener", handlers=False)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_TTL,
                255
            )
        self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(self.addr) + socket.inet_aton("0.0.0.0")
            )

        self.sock.settimeout(1)

        while self.should_run:
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.error:
                pass
            else:
                print (data)
                self.parse_message(data.decode("ascii"))

            if time.time() - self.last_msg < 3:
                continue

            self.listen_ws()

        logging.debug("Listener halted", handlers=False)
        self.halted = True


    def listen_ws(self):
        url = config["hub"] + "/" + "mesg"




    def parse_message(self, data, addr=False):
        try:
            message = SeismicMessage(json.loads(data))
        except Exception:
            log_traceback(handlers=False)
            logging.debug("Malformed seismic message detected: {}".format(data))
            return

        if message.site_name != self.site_name:
            return
        if addr:
            message.address = addr
        self.last_msg = time.time()

        if message.method == "objects_changed":
            for i, m in enumerate(self.queue):
                if m.method == "objects_changed" and m.data["object_type"] == message.data["object_type"]:
                    r = list(set(m.data["objects"] + message.data["objects"] ))
                    self.queue[i].data["objects"] = r
                    break
            else:
                self.queue.append(message)

        elif message.method == "playout_status":
            for i, m in enumerate(self.queue):
                if m.method == "playout_status":
                    self.queue[i] = message
                    break
            else:
                self.queue.append(message)
        else:
            self.queue.append(message)


    def halt(self):
        logging.debug("Shutting down listener")
        self.should_run = False
