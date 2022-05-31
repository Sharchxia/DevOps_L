import pymysql
from typing import List
from sanic import Sanic
import json as js
import random
import hashlib
import string
from sanic.log import logger


class MySQL:
    def __init__(self, host='127.0.0.1', user='root', passwd='123456', database='dev_test'):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=self.database)
        self.cur = self.db.cursor()

    def __del__(self):
        self.cur.close()
        self.db.close()

    def commit(self):
        self.db.commit()

    def roll_back(self):
        self.db.rollback()

    def my_add(self, table: str, columns: str, values: str):
        command = '''insert into {} ({}) values ({})'''.format(table, columns, values)
        self.cur.execute(command)

    def my_delete(self, table, condition: str):
        command = '''delete from {} where {}'''.format(table, condition)
        self.cur.execute(command)

    def my_scan(self, table: str, columns='*', condition=None):
        if condition is None:
            command = '''select {} from {}'''.format(columns, table)
        else:
            command = '''select {} from {} where {}'''.format(columns, table, condition)
        logger.info(command)
        self.cur.execute(command)
        data = self.cur.fetchall()
        return data

    def my_update(self, table: str, column: List[str], value: List[str], condition: str):
        target = ''
        for i in range(len(column)):
            target += column[i] + '=' + "'" + value[i] + "'" + ','
        target = target[:-1]
        if len(target) != 0:
            command = '''update {} set {} where {}'''.format(table, target, condition)
            self.cur.execute(command)


def encrypt(passwd: str):
    seed = ord(passwd[-1])
    random.seed(seed)
    salt = random.sample(string.digits, 5)
    salt = ''.join(salt)
    passwd = passwd[int(len(passwd)/2):] + passwd[:int(len(passwd)/2)]
    md5 = hashlib.md5(salt.encode('utf-8'))
    md5.update(passwd.encode('utf-8'))
    ret = md5.hexdigest()
    return ret


available = {}
CER = 'dev_device_certification'


app = Sanic('south')


@app.websocket('/south')
async def operation(rq, ws):
    while True:
        with open('return_info.json', 'r') as f:
            ret = js.load(f)
        msgs = await ws.recv()
        msgs = js.loads(msgs)
        op = msgs['operation']
        if op == 'a':
            ret = check(msgs, ret)
        elif op == 'p' and msgs['cer'] in available:
            ret = get_info(msgs, ret)
        elif op == 'c' and msgs['cer'] in available:
            ret = control(msgs, ret)
        else:
            ret['warning'] = 'permission denied'
            ret = js.dumps(ret)
        await ws.send(ret)


def check(msgs, ret):
    my = MySQL()
    uid = msgs['msgs']['uid']
    passwd = encrypt(msgs['msgs']['passwd'])
    condition = '''id='{}' and passwd='{}\''''.format(uid, passwd)
    if len(my.my_scan(CER, condition=condition)):
        available[uid] = dict()
        available[uid]['reboot'] = '0'
        available[uid]['sftp'] = '0'
        ret['authenticated'] = '1'
    ret = js.dumps(ret)
    return ret


def get_info(msgs, ret):
    my = MySQL()
    logger.info(msgs['cer'])
    logger.info(msgs['msgs'])
# there is left for operating SQL, maybe
    ret['pushed'] = '1'
    ret = js.dumps(ret)
    return ret


def control(msgs, ret):
    uid = msgs['cer']
    if int(available[uid]['reboot']):
        ret['command'] = 'r'
        available[uid]['reboot'] = '0'
    elif int(available[uid]['sftp']):
        ret['command'] = 's'
        available[uid]['sftp'] = '0'
    ret = js.dumps(ret)
    return ret


if __name__ == '__main__':
    app.run('127.0.0.1', 8000)
