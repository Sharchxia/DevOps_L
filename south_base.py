import websocket as wb
import time
import json as js
import os
import psutil as ps
import shutil
import uuid
import socket
from pathlib import Path


def get_now():
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return t


def status():
    gb = 1024 ** 3
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return {
        'cpu_count': ps.cpu_count(logical=False),
        'cup_percent': ps.cpu_percent(),
        'mem_total': str(round((float(ps.virtual_memory().total) / 1024 / 1024 / 1024), 2)) + "G",
        'mem_percent': str(ps.virtual_memory().percent) + '%',
        'disk_total': '{:6.2f} GB '.format(shutil.disk_usage('/')[0] / gb),
        'disk_leave': '{:6.2f} GB '.format(shutil.disk_usage('/')[2] / gb),
        'disk_percent': '{:6.2f} % '.format(shutil.disk_usage('/')[1] / shutil.disk_usage('/')[0]),
        'mac_address': ":".join([mac[e:e + 2] for e in range(0, 11, 2)]),
        'ip_address': socket.gethostbyname(socket.gethostname())
    }


class SouthBase:
    def __init__(self, ip='127.0.0.1', port='8002', target='/south'):
        self.ip = ip
        self.port = port
        self.__if_connected = 0
        self.__if_authenticated = 0
        self.__if_pushed = 0
        self.__url = 'ws://' + ip + ':' + port + target
        self.__ask_times = 0
        self.__push_times = 100
        self.__command = ''
        self.__uid = ''
        self.log_file = './south_base.json'
        self.json = './operation.json'
        self.ws = wb.WebSocket()
        if not Path(self.log_file).is_file():
            data = {get_now(): 'create this file'}
            with open(self.log_file, 'w+') as f:
                js.dump(data, f, indent=2)

    def __del__(self):
        self.ws.close()
        if self.__command == 'r':
            os.system('shutdown -t 1 -r')

    def recv(self):
        try:
            data = self.ws.recv()
            data = js.loads(data)
            return data
        except Exception as e:
            print('\033[0;32mSome error happens in the server\033[0m')
            print(e)
            self.__del__()

    def log(self, event: int):  # 1 means connect, 2->establish tube, 3->authenticate, 4->push status data
        if event not in [1, 2, 3, 4]:
            return
        with open(self.log_file, 'r') as f:
            data = js.load(f)
        try:
            data[get_now()]
        except:
            data[get_now()] = dict()
        if event == 1:
            data[get_now()]['connect'] = 'try to connect to server'
        elif event == 2:
            if self.__if_connected:
                data[get_now()]['channel'] = 'connect to server successfully'
            else:
                data[get_now()]['channel'] = 'cannot find server, please check if server is closed'
        elif event == 3:
            if self.__if_authenticated:
                data[get_now()]['authentication'] = 'device is allowed to communicate with the server'
            else:
                data[get_now()]['authentication'] = 'permission denied, please check the UID and PASSWORD'
        else:
            if self.__if_pushed:
                data[get_now()]['push'] = 'pushed the status data successfully'
            else:
                data[get_now()]['push'] = 'failed to push data to server'

        with open(self.log_file, 'w') as f:
            js.dump(data, f, indent=2)

    def connect(self):
        self.ws.connect(self.__url)

    def run(self):
        self.log(1)
        try:
            self.connect()
            self.__if_connected = 1
            self.log(2)
        except Exception as e:
            self.__if_connected = 0
            print('\033[0;31mFailed to connect to the server\033[0m')
            print(e)
            self.log(2)
            return
        self.authenticate()
        ret = int(self.recv()['authenticated'])
        if not ret:
            self.__if_authenticated = 0
            self.log(3)
            print('\033[0;31mPermission denied\033[0m')
            return
        self.__if_authenticated = 1
        self.log(3)
        while True:
            if self.__ask_times == 100 - self.__push_times:
                self.send_status()
                ret = int(self.recv()['pushed'])
                if ret:
                    self.__if_pushed = 1
                else:
                    self.__if_pushed = 0
                self.log(4)
            self.ask_cmd()
            ret = self.recv()['command']
            if ret == 'r':
                self.__command = 'r'
                return
            elif ret == 's':
                pass
            time.sleep(2)

    def authenticate(self):
        print('Please enter \033[0;31mUID\033[0m')
        uid = input()
        self.__uid = uid
        print('Please enter \033[0;31mPASSWORD\033[0m')
        passwd = input()
        print(uid, passwd)
        with open(self.json) as f:
            template = js.load(f)
        template['operation'] = 'a'
        template['msgs']['uid'] = uid
        template['msgs']['passwd'] = passwd
        data = js.dumps(template)
        self.ws.send(data)
        time.sleep(0.02)

    def send_status(self):
        with open(self.json) as f:
            template = js.load(f)
        template['operation'] = 'p'
        template['msgs'] = status()
        template['cer'] = self.__uid
        data = js.dumps(template)
        self.ws.send(data)
        time.sleep(0.02)

    def ask_cmd(self):
        with open(self.json) as f:
            template = js.load(f)
        template['operation'] = 'c'
        template['cer'] = self.__uid
        data = js.dumps(template)
        self.ws.send(data)
        time.sleep(0.02)


if __name__ == '__main__':
    south = SouthBase(port='8001')
    south.run()