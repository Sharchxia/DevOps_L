import time

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

    def my_delete(self, table: str, condition: str):
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

    def my_truncate(self, table: str):
        command = "truncate table {}".format(table)
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
CHECK = 'dev_check_cmd'

COLUMNS_CHECK = ['id', 'reboot', 'sftp', 'sftp_position']

app = Sanic('south')


@app.websocket('/south')
async def operation(rq, ws):
    global available
    while True:
        with open('return_info.json', 'r') as f:
            ret = js.load(f)
        msgs = await ws.recv()
        msgs = js.loads(msgs)
        op = msgs['operation']
        uid = msgs['cer']
        if uid in available.keys():
            available[uid]['time2'] = time.time()
            if available[uid]['time2'] - available[uid]['time1'] > 10:
                available = available.pop(uid)
                my = MySQL()
                try:
                    condition = "id='{}'".format(uid)
                    my.my_delete(CHECK, condition)
                    my.commit()
                except:
                    logger.info('eeeeeeeeeeeeeeeeeee')
                    my.roll_back()
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
    global available
    my = MySQL()
    uid = msgs['msgs']['uid']
    passwd = encrypt(msgs['msgs']['passwd'])
    condition = '''id='{}' and passwd='{}\''''.format(uid, passwd)
    if len(my.my_scan(CHECK, condition="id='{}'".format(uid))):
        try:
            my.my_delete(CHECK, condition="id='{}'".format(uid))
            my.commit()
        except Exception as e:
            my.roll_back()
            logger.info('\033[0;31mError: {}\033[0m'.format(str(e)))
    if len(my.my_scan(CER, condition=condition)):
        available[uid] = dict()
        available[uid]['reboot'] = '0'
        available[uid]['sftp'] = '0'
        available[uid]['time1'] = time.time()
        available[uid]['time2'] = time.time()
        ret['authenticated'] = '1'
        columns = ','.join(COLUMNS_CHECK)
        value = ','.join([uid, '0', '0', '0'])
        try:
            my.my_add(CHECK, columns, value)
            my.commit()
        except Exception as e:
            my.roll_back()
            logger.info('\033[0;31mError: {}\033[0m'.format(str(e)))
    ret = js.dumps(ret)
    return ret


def get_info(msgs, ret):
    # my = MySQL()
    logger.info({msgs['cer']: msgs['msgs']})
    # logger.info(msgs['msgs'])
    # there is left for operating SQL, maybe
    ret['pushed'] = '1'
    ret = js.dumps(ret)
    return ret


def control(msgs, ret):
    global available
    uid = msgs['cer']
    my = MySQL()
    condition = "id='{}'".format(uid)
    cmd = my.my_scan(CHECK, condition=condition)[0]
    available[uid]['time1'] = time.time()
    try:
        if len(cmd):
            available[uid]['reboot'] = cmd[1]
            available[uid]['sftp'] = cmd[2]
        if int(available[uid]['reboot']):
            ret['command'] = 'r'
            available[uid]['reboot'] = '0'
            my.my_update(CHECK, COLUMNS_CHECK[1:2], ['0'], condition)
        elif int(available[uid]['sftp']):
            ret['command'] = 's'
            ret['position'] = cmd[3]
            available[uid]['sftp'] = '0'
            my.my_update(CHECK, COLUMNS_CHECK[2:3], ['0'], condition)
        my.commit()
    except Exception as e:
        logger.info('\033[0;31mError: {}\033[0m'.format(str(e)))
        my.roll_back()
    ret = js.dumps(ret)
    return ret


if __name__ == '__main__':
    m = MySQL()
    try:
        m.my_truncate(CHECK)
        m.commit()
        app.run('0.0.0.0', 8001)
    except Exception as er:
        m.roll_back()
        print('Error: %s' % str(er))
