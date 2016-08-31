import json
import socket
import time
import requests

from urllib.request import urlopen

from firefly_common import *

def readlines(f):
    buff = b""
    for ch in f.iter_content(1):
        ch = ch
        if ch == b"\n":
            yield buff.decode("ascii")
            buff = b""
        else:
            buff+=ch
    yield buff.decode("ascii")


class SeismicMessage(object):
    def __init__(self, packet):
        self.timestamp, self.site_name, self.host, self.method, self.data = packet


class SeismicListener(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self._halt = False
        self.halted = True
        self.queue = []

    def listen(self, site_name, addr, port):
        self.site_name = site_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0",port))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        status = self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(addr) + socket.inet_aton("0.0.0.0"));
        self.sock.settimeout(1)
        self.start()

    def run(self):
        logging.info("Starting Seismic listener")
        self.halted = False
        self.last_msg = time.time()
        while not self._halt:
            try:
                data, addr = self.sock.recvfrom(1024)
            except (socket.error):
                pass
            else:
                self.parse_message(data)
            if time.time() - self.last_msg < 3:
                continue
            self.listen_http()
        logging.debug("Listener halted")
        self.halted = True

    def listen_http(self):
        host = config.get("host", None)

        url = "{host}/{target}".format(
                host=host,
                target="msg_subscribe?id={}".format(config["site_name"])
            )

        try:
            request = requests.get(
                    url,
                    stream=True,
                )
        except:
            log_traceback("Seismic HTTP request failed")
            return

        for line in readlines(request):
            if self._halt:
                return
            if line:
                self.parse_message(line)


    def parse_message(self, data, addr=False):
        try:
            message = SeismicMessage(json.loads(data))
        except:
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
        self._halt = True

    def add_handler(self, handler):
        self.signal.sig.connect(handler)
