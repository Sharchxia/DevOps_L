import random
import string
import hashlib
import pymysql
from typing import List


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

def get_key():
    my = MySQL()
    passwords = my.my_scan(table='dev_device_certification', columns='passwd')
    my_range = string.ascii_letters + string.digits + string.punctuation
    my_range = my_range.replace('\'', '')
    my_range = my_range.replace('\"', '')
    my_range = my_range.replace('\\', '')
    key = random.sample(my_range, 80)
    key = ''.join(key)
    while key in passwords:
        key = ''.join(random.sample(my_range, 80))
    return key


def encrypt(passwd: str):
    seed = ord(passwd[-1])
    random.seed(seed)
    salt = random.sample(string.digits, 5)
    salt = ''.join(salt)
    passwd = passwd[41:] + passwd[:41]
    md5 = hashlib.md5(salt.encode('utf-8'))
    md5.update(passwd.encode('utf-8'))
    ret = md5.hexdigest()
    return ret


if __name__ == '__main__':
    ret = encrypt('~oyPJ*0Ta[=Dk|X:mltSZHB92e_i!x75}h/MbsjgdROqW3;I.Y1r^?VF@+6${v#-CU4NGf)K`p8>&E(z')
    print(ret)
    print(type(ret))
    print(len(ret))
