from typing import List
import sys
import pymysql
from sanic.log import logger


class MySQL:
    def __init__(self, host='127.0.0.1', user='root', passwd='', database='dev_test'):
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

    def my_truncate(self, table: str):
        command = "truncate table {}".format(table)
        self.cur.execute(command)


CHECK = 'dev_check_cmd'
COLUMNS_CHECK = ['id', 'reboot', 'sftp', 'sftp_position']

# give (or change) flags of command in SQL
# enter format should be:
# reboot: python3 give_cmd uid reboot
# sftp: python3 give_cmd uid sftp position
if __name__ == "__main__":
    my = MySQL()
    uid = sys.argv[1]
    operation = sys.argv[2]
    cond = "id='{}'".format(uid)
    existing = my.my_scan(CHECK, condition=cond)
    if not len(existing):
        print('No such a device could receive the command')
    else:
        try:
            if operation == 'reboot':
                my.my_update(CHECK, COLUMNS_CHECK[1:2], ['1'], cond)
            elif operation == 'sftp':
                position = sys.argv[3]
                my.my_update(CHECK, COLUMNS_CHECK[2:], ['1', position], cond)
            print('give command successfully')
            my.commit()
        except Exception as e:
            print('\033[0;31mError: {}\033[0m'.format(str(e)))
            my.roll_back()
