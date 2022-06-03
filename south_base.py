import paramiko
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
    def __init__(self, ip='127.0.0.1', port='8000', target='/south'):
        self.ip = ip
        self.port = port
        self.__if_connected = 0
        self.__if_authenticated = 0
        self.__if_pushed = 0
        self.__url = 'ws://' + ip + ':' + port + target
        self.__ask_times = 100
        self.__push_times = 100
        self.__command = ''
        self.__uid = ''
        self.__target_ip = self.ip
        self.__target_name = 'root'
        self.__target_passwd = 'Fxxc524466'
        self.log_file = './log_info.json'
        self.json = './operation.json'
        self.ws = wb.WebSocket()
        if not Path(self.log_file).is_file():
            data = {get_now(): {'initialise': 'create this log file'}}
            with open(self.log_file, 'w') as f:
                js.dump(data, f, indent=2)

    def __del__(self):
        self.ws.close()
        # print(self.__command)
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
            del self  # if server has error, killing this client is a good choice

    def log(self, event: int):  # 1 means connect, 2->establish tube, 3->authenticate, 4->push status data
        if event not in [1, 2, 3, 4, 5, 6]:
            return
        with open(self.log_file, 'r') as f:
            data = js.load(f)
        try:
            data[get_now()] = data[get_now()]
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
        elif event == 4:
            if self.__if_pushed:
                data[get_now()]['push'] = 'pushed the status data successfully'
            else:
                data[get_now()]['push'] = 'failed to push data to server'
        elif event == 5:
            data[get_now()]['sftp'] = 'pushed the log file successfully'
        else:
            data[get_now()]['sftp'] = 'failed to push the log file'

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
            if self.__ask_times >= self.__push_times:
                self.send_status()
                ret = int(self.recv()['pushed'])
                if ret:
                    self.__if_pushed = 1
                else:
                    self.__if_pushed = 0
                self.log(4)
                self.__ask_times = 0
            self.ask_cmd()
            self.__ask_times += 1
            ret = self.recv()
            if 'warning' in ret.keys():
                print('\033[0;31mPermission denied\033[0m')
                self.__command = ''
                return
            if ret['command'] == 'r':
                self.__command = 'r'
                self.__del__()
                return
            elif ret['command'] == 's':
                try:
                    client = paramiko.Transport((self.__target_ip, 22))
                    client.connect(username=self.__target_name, password=self.__target_passwd)
                    sftp = paramiko.SFTPClient.from_transport(client)
                    position = ret['position']
                    sftp.put(localpath=self.log_file, remotepath=position + '/' + self.__uid + '_' + self.log_file)
                    print('sftp run successfully')
                    data = {'msgs': {'Done': 'sftp log file of device successfully'}, 'cmd': 'p', 'cer': self.__uid}
                    data = js.dumps(data)
                    self.ws.send(data)
                    self.log(5)
                    time.sleep(0.02)
                    self.recv()
                except:
                    data = {'msgs': {'Error': 'fail to sftp log file of device '}, 'cmd': 'p', 'cer': self.__uid}
                    data = js.dumps(data)
                    self.ws.send(data)
                    print('fail to run sftp')
                    self.log(6)
                    time.sleep(0.02)
                    self.recv()
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
        template['cer'] = uid
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


# run this code and follow red tips given to operation correctly
if __name__ == '__main__':
    south = SouthBase(ip='120.77.73.107')
    south.run()
