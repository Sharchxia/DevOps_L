import pymysql
import snowflake.client
import random
import string
import time
import hashlib
from sanic import Sanic
from sanic.response import json
from sanic.log import logger
from typing import List
import ssl

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("ca.crt", keyfile="ca.key")

BASE = 'dev_device_info_base'
HARD = 'dev_device_info_hardware'
SOFT = 'dev_device_info_software'
CER = 'dev_device_certification'
GROUP_DEVICE = 'dev_group_and_device'
GROUP_INFO = 'dev_group_info'
CHECK = 'dev_check_cmd'


COLUMNS_BASE = ['id', 'name', 'description', 'time_create', 'time_update']
COLUMNS_HARD = ['id', 'hard_number', 'hard_type', 'efi_mac', 'wifi_mac', 'lte']
COLUMNS_SOFT = ['id', 'base_version', 'base_update_time', 'base_status', 'service_version', 'service_update_time',
                'service_status']
COLUMNS_CER = ['id', 'passwd']
COLUMNS_GROUP_DEVICE = ['group_id', 'device_id']
COLUMNS_GROUP_INFO = ['id', 'name', 'description', 'time_create', 'time_update', 'content']
COLUMNS_CHECK = ['id', 'reboot', 'sftp', 'sftp_position']


class MySQL:
    def __init__(self, host='127.0.0.1', user='root', passwd='', database='dev_test'):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=self.database)
        self.cur = self.db.cursor()

    def __del__(self):  # ensure database would be close
        self.cur.close()
        self.db.close()

    def commit(self):
        self.db.commit()

    def roll_back(self):
        self.db.rollback()

    def my_add(self, table: str, columns: str, values: str):  # add new row into a table
        command = '''insert into {} ({}) values ({})'''.format(table, columns, values)
        self.cur.execute(command)

    def my_delete(self, table, condition: str):  # delete a row meeting condition in table
        command = '''delete from {} where {}'''.format(table, condition)
        self.cur.execute(command)

    def my_scan(self, table: str, columns='*', condition=None):  # get info from table based on condition
        if condition is None:
            command = '''select {} from {}'''.format(columns, table)
        else:
            command = '''select {} from {} where {}'''.format(columns, table, condition)
        self.cur.execute(command)
        data = self.cur.fetchall()
        return data

    def my_update(self, table: str, column: List[str], value: List[str], condition: str):
        # update info based on condition
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

def get_key():
    my = MySQL()
    passwords = my.my_scan(table='dev_device_certification', columns='passwd')
    my_range = string.ascii_letters + string.digits + string.punctuation
    my_range = my_range.replace('\'', '')
    my_range = my_range.replace('\"', '')
    my_range = my_range.replace('\\', '')
    my_range = my_range.replace(' ', '')
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
    passwd = passwd[int(len(passwd)/2):] + passwd[:int(len(passwd)/2)]
    md5 = hashlib.md5(salt.encode('utf-8'))
    md5.update(passwd.encode('utf-8'))
    ret = md5.hexdigest()
    return ret


def get_uid():
    host = 'localhost'
    port = 8910
    snowflake.client.setup(host, port)
    uid = snowflake.client.get_guid()
    return uid


def get_now():
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return t


app = Sanic('test')


@app.post('/device_new')
async def dev_new(request):
    my = MySQL()
    snowflake.client.setup('localhost', 8910)
    existing_name = my.my_scan(BASE, COLUMNS_BASE[1])
    existing_name = tuple(*zip(*existing_name))
    content = request.form
    # logger.info(content)
    try:
        name = content['name'][0]
    except:
        return json({'status': 'Error, invalid name'}, status=400)
    if name in existing_name:
        return json({'status': 'device exists'}, status=400)
    else:
        uid = str(get_uid())
        try:
            description = content['description'][0]
        except:
            description = ''
        time_create = get_now()
        time_update = time_create
        base_columns = ','.join(COLUMNS_BASE)
        base = [uid, name, description, time_create, time_update]
        base = "'{}', '{}', '{}', '{}', '{}'".format(*base)
        base_version = '1.00'
        base_update_time = time_create
        base_status = 'good'
        service_version = '1.00'
        service_update_time = time_create
        service_status = 'good'
        software_columns = ','.join(COLUMNS_SOFT)
        software = [uid, base_version, base_update_time, base_status, service_version, service_update_time,
                    service_status]
        software = "'{}', '{}', '{}', '{}', '{}', '{}', '{}'".format(*software)
        try:
            hard_number = content['hard_number'][0]
        except:
            hard_number = ''
        try:
            hard_type = content['hard_type'][0]
        except:
            hard_type = ''
        try:
            efi_mac = content['efi_mac'][0]
        except:
            efi_mac = ''
        try:
            wifi_mac = content['wifi_mac'][0]
        except:
            wifi_mac = ''
        try:
            lte = content['lte'][0]
        except:
            lte = ''
        hardware_columns = ','.join(COLUMNS_HARD)
        hardware = [uid, hard_number, hard_type, efi_mac, wifi_mac, lte]
        hardware = "'{}', '{}', '{}', '{}', '{}', '{}'".format(*hardware)
        passwd_ret = get_key()
        passwd_store = encrypt(passwd_ret)
        certification_columns = ','.join(COLUMNS_CER)
        certification = [uid, passwd_store]
        certification = "'{}', '{}'".format(*certification)
        try:
            my.my_add(BASE, base_columns, base)
            my.my_add(SOFT, software_columns, software)
            my.my_add(HARD, hardware_columns, hardware)
            my.my_add(CER, certification_columns, certification)
            my.commit()
            logger.info('Done, a new device is added')
            return json({'status': 'Done', 'info': {'device_id': uid, 'base': {'name': name, 'description': description,
                                                                               'time_create': time_create,
                                                                               'time_update': time_update},
                                                    'hardware': {'hard_number': hard_number,
                                                                 'hard_type': hard_type, 'efi_mac': efi_mac,
                                                                 'wifi_mac': wifi_mac, 'lte': lte}, 'software': {
                    'base_version': base_version, 'base_update_time': base_update_time, 'base_status': base_status,
                    'service_version': service_version, 'service_update_time': service_update_time,
                    'service_status': service_status},
                                                    'certification': passwd_ret}})
        except Exception as e:
            logger.info('\033[0;31mError: fail to add a new device because: {}\033[0m'.format(str(e)))
            my.roll_back()
            return json({'status': 'Error, please try again'}, status=400)


@app.post('/device_del')
async def delete(request):
    content = request.form
    try:
        uid = content['device_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'})
    my = MySQL()
    condition = '''id = \'{}\''''.format(uid)
    if len(my.my_scan(BASE, condition=condition)) == 0:
        return json({'status': 'Error', 'info': 'no such device'})
    try:
        my.my_delete(BASE, condition)
        my.my_delete(HARD, condition)
        my.my_delete(SOFT, condition)
        my.my_delete(CER, condition)
        my.commit()
        logger.info('Done, a device has been deleted')
        return json({'status': 'Done', 'info': 'device has been deleted successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError: fail to delete the device because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/device_scan')
async def dev_scan(request):
    content = request.form
    try:
        uid = content['device_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition = '''id=\'{}\''''.format(uid)
    base = my.my_scan(BASE, condition=condition)[0]
    if len(base) == 0:
        return json({'status': 'Error', 'info': 'no such device'}, status=400)
    hard = my.my_scan(HARD, condition=condition)[0]
    soft = my.my_scan(SOFT, condition=condition)[0]
    cer = my.my_scan(CER, condition=condition)[0]
    try:
        logger.info('return information successfully')
        return json({'status': 'Done', 'info': {'device_id': uid, 'base': {'name': base[1], 'description': base[2],
                                                                           'time_create': str(base[3]),
                                                                           'time_update': str(base[4])},
                                                'hardware': {'hard_number': hard[1],
                                                             'hard_type': hard[2], 'efi_mac': hard[3],
                                                             'wifi_mac': hard[4], 'lte': hard[5]}, 'software': {
                'base_version': soft[1], 'base_update_time': str(soft[2]), 'base_status': soft[3],
                'service_version': soft[4], 'service_update_time': str(soft[5]),
                'service_status': soft[6]},
                                                'certification': cer[1]}})
    except Exception as e:
        logger.info('\033[0;31mError: fail to get info of the device because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/device_update')
async def dev_update(request):
    content = request.form
    try:
        uid = content['device_id'][0]
    except:
        return json({'status': 'Error', 'info': 'validated input'}, status=400)
    base = [''] * 4
    try:
        base[0] = content['name'][0]
    except:
        pass
    try:
        base[1] = content['description'][0]
    except:
        pass
    # base = list(content['base'].values())
    hard = [''] * 5
    try:
        hard[0] = content['hard_number'][0]
    except:
        pass
    try:
        hard[1] = content['hard_type'][0]
    except:
        pass
    try:
        hard[2] = content['efi_mac'][0]
    except:
        pass
    try:
        hard[3] = content['wifi_mac'][0]
    except:
        pass
    try:
        hard[4] = content['lte'][0]
    except:
        pass
    # hard = list(content['hardware'].values())
    # soft = list(content['software'].values())
    soft = [''] * 6
    try:
        soft[0] = content['base_version'][0]
    except:
        pass
    try:
        soft[2] = content['base_status'][0]
    except:
        pass
    try:
        soft[3] = content['service_version'][0]
    except:
        pass
    try:
        soft[5] = content['service_status'][0]
    except:
        pass
    now = get_now()
    base[3] = now
    soft[1] = now
    soft[4] = now
    my = MySQL()
    condition = '''id=\'{}\''''.format(uid)
    if len(my.my_scan(BASE, condition=condition)) == 0:
        return json({'status': 'Error', 'info': 'no such device'}, status=400)
    try:
        columns_base = []
        value_base = []
        for i in base:
            if i != '':
                columns_base += [COLUMNS_BASE[1:][base.index(i)]]
                value_base += [i]
        columns_hard = []
        value_hard = []
        for i in hard:
            if i != '':
                columns_hard += [COLUMNS_HARD[1:][hard.index(i)]]
                value_hard += [i]
        columns_soft = []
        value_soft = []
        for i in soft:
            if i != '':
                columns_soft += [COLUMNS_SOFT[1:][soft.index(i)]]
                value_soft += [i]
        my.my_update(BASE, columns_base, value_base, condition)
        my.my_update(SOFT, columns_soft, value_soft, condition)
        my.my_update(HARD, columns_hard, value_hard, condition)
        my.commit()
        logger.info('information of a device has been modified successfully')
        return json({'status': 'Done', 'info': 'update successfully'})
    except Exception as e:
        logger.info('\033[0;31mError: fail to update the new device because: {}\033[0m'.format(str(e)))
        my.roll_back()
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.get('/scan_all_device')
async def scan_all_dev(request):
    my = MySQL()
    ret = dict()
    base = my.my_scan(BASE)
    if len(base) == 0:
        return json({'status': 'Warning', 'info': 'no date in tables'}, status=400)
    try:
        for i in base:
            number = 'device_{}'.format(str(base.index(i) + 1))
            ret[number] = {'device_id': i[0], 'base': {'name': i[1], 'description': i[2], 'time_create': str(i[3]),
                                                       "time_update": str(i[4])}}
        logger.info('all devices\' info has been return')
        return json({'status': 'Done', 'info': ret})
    except Exception as e:
        logger.info('\033[0;31mError: fail to return info because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


@app.post('/device_id_group')
async def dev_id_group(request):
    my = MySQL()
    content = request.form
    try:
        uid = content['device_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'}, status=400)
    condition = '''id=\'{}\''''.format(uid)
    try:
        base = my.my_scan(BASE, condition=condition)[0]
        if len(base) == 0:
            return json({'status': 'Error', 'info': 'No such device'})
        condition = '''device_id=\'{}\''''.format(uid)
        group_id = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[0], condition)
        group_id = tuple(*zip(*group_id))
        if len(group_id) == 0:
            group_info = 'No group available'
        else:
            group_info = dict()
            for i in group_id:
                condition = '''id=\'{}\''''.format(i)
                info = my.my_scan(GROUP_INFO, condition=condition)
                info = {'group_id': info[0], 'name': info[1], 'description': info[2], 'time_create': info[3],
                        'time_update': info[4], 'content': info[5]}
                group_info['group{}'.format(str(group_id.index(i) + 1))] = info
        logger.info('Done, info of device and corresponding group has been returned')
        return json({'status': 'Done', 'info': {'base': {'name': base[1], 'description': base[2],
                                                         'time_create': str(base[3]), 'time_update': str(base[4])},
                                                'groups': group_info}})
    except Exception as e:
        logger.info('\033[0;31mError, fail to return info because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.get('/scan_all_device_group')
async def scan_all_device_group(request):
    my = MySQL()
    base = my.my_scan(BASE)
    if len(base) == 0:
        return json({'status': 'Warning', 'info': 'no data in tables'}, status=400)
    device_ids = my.my_scan(BASE, COLUMNS_BASE[0])
    device_ids = tuple(*zip(*device_ids))
    info = dict()
    try:
        for i in device_ids:
            condition = '''device_id=\'{}\''''.format(i)
            group_ids = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[0], condition=condition)
            group_ids = tuple(*zip(*group_ids))
            ind = device_ids.index(i)
            number = 'device{}'.format(str(ind + 1))
            info[number] = {'device_id': base[ind][0], 'base': {'name': base[ind][1], 'description': base[ind][2],
                                                                'time_create': str(base[ind][3]),
                                                                'time_update': str(base[ind][4])
                                                                }, 'groups_id': group_ids}
        logger.info('all devices and their groups are returned')
        return json({'status': 'Done', 'info': info})
    except Exception as e:
        logger.info('\033[0;31mError, fail to return info because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/group_new')
async def group_new(request):
    content = request.form
    try:
        name = content['name'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid name'}, status=400)
    uid = str(get_uid())
    try:
        description = content['description'][0]
    except:
        description = ''
    now = get_now()
    time_create = now
    time_update = now
    device_num = '0'
    if len(name) == 0:
        return json({'status': 'Warning', 'info': 'invalid name'}, status=400)
    my = MySQL()
    existing_group = tuple(*zip(*(my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[1]))))
    if name in existing_group:
        return json({'status': 'Warning', 'info': 'group already exists'}, status=400)
    try:
        columns = ','.join(COLUMNS_GROUP_INFO)
        values = "'{}', '{}', '{}', '{}', '{}', '{}'".format(uid, name, description, time_create, time_update,
                                                             device_num)
        my.my_add(GROUP_INFO, columns, values)
        my.commit()
        logger.info('a new group has been added')
        return json({'status': 'Done', 'info': {'group_id': uid, 'name': name, 'description': description,
                                                'time_create': time_create, 'time_update': time_update,
                                                'device_num': device_num}})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to add a new group because: {}\033[0m '.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/group_del')
async def group_del(request):
    content = request.form
    try:
        uid = content['group_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition = 'id=\'{}\''.format(uid)
    if len(my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[0], condition)) == 0:
        return json({'status': 'Warning', 'info': 'no such a group'}, status=400)
    try:
        my.my_delete(GROUP_INFO, condition)
        condition = "group_id='{}'".format(uid)
        my.my_delete(GROUP_DEVICE, condition)
        my.commit()
        logger.info('a group has been deleted successfully')
        return json({'status': 'Done', 'info': 'delete group successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to delete a group because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/group_scan')
async def group_scan(request):
    content = request.form
    try:
        uid = content['group_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition = "id='{}'".format(uid)
    info = my.my_scan(GROUP_INFO, condition=condition)[0]
    if len(info) == 0:
        return json({'status': 'Warning', 'info': 'no such a group'}, status=400)
    try:
        condition = "group_id='{}'".format(uid)
        logger.info('return info of the group successfully')
        device_ids = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[1], condition)
        device_ids = tuple(*zip(*device_ids))
        including_devices_id = dict()
        for i in device_ids:
            number = 'device_{}'.format(str(device_ids.index(i) + 1))
            including_devices_id[number] = i
        logger.info('return info of group successfully')
        return json({'status': 'Done', 'info': {'group_id': uid, 'name': info[1], 'description': info[2],
                                                'time_create': str(info[3]), 'time_update': str(info[4]), 'device_num':
                                                    info[5], 'including_device_id': including_devices_id}})
    except Exception as e:
        logger.info('\033[0;31mError, fail to return info of group because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/group_update')
async def group_update(request):
    content = request.form
    try:
        uid = content['group_id'][0]
    except:
        return json({'status': 'Error', 'info': 'invalid input'}, status=400)
    condition = "id='{}'".format(uid)
    my = MySQL()
    if len(my.my_scan(GROUP_INFO, condition=condition)) == 0:
        return json({'status': 'Warning', 'info': 'no such a group'}, status=400)
    data = ['']*7
    data[0] = uid
    try:
        data[1] = content['name'][0]
    except:
        pass
    try:
        data[2] = content['description'][0]
    except:
        pass
    # data = list(content.values())
    columns_group_info = []
    values = []
    for info in data[:-1]:
        if info != '':
            columns_group_info += [COLUMNS_GROUP_INFO[data.index(info)]]
            values += [info]
    time_update = get_now()
    columns_group_info.append(COLUMNS_GROUP_INFO[4])
    values.append(time_update)
    try:
        my.my_update(GROUP_INFO, columns_group_info, values, condition)
        my.commit()
        logger.info('update info of the group successfully')
        return json({'status': 'Done', 'info': 'update the group successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to update group because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.get('/scan_all_group')
async def scan_all_group(request):
    my = MySQL()
    device_ids = my.my_scan(BASE, COLUMNS_BASE[0])
    device_ids = tuple(*zip(*device_ids))
    group_ids = my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[0])
    group_ids = tuple(*zip(*group_ids))
    if len(device_ids) and len(group_ids) == 0:
        return json({'status': 'Warning', 'info': 'few data in tables'}, status=400)
    try:
        device = dict()
        for device_id in device_ids:
            condition = "device_id='{}'".format(device_id)
            groups = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[0], condition)
            groups = tuple(*zip(*groups))
            number = "device_{}".format(str(device_ids.index(device_id) + 1))
            device[number] = {'device_id': device_id, 'groups': groups}
        group = dict()
        for group_id in group_ids:
            condition = "group_id='{}'".format(group_id)
            devices = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[1], condition)
            devices = tuple(*zip(*devices))
            number = "group_{}".format(str(group_ids.index(group_id) + 1))
            group[number] = {'group_id': group_id, 'device_ids': devices}
        logger.info('return info of relationship of groups and devices successfully')
        return json({'status': 'Done', 'info': {'devices': device, 'groups': group}})
    except Exception as e:
        logger.info('\033[0;31mError, fail to return relation of groups and devices because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'}, status=400)


@app.post('/group_new_device')
async def group_new_device(request):
    content = request.form
    try:
        group_id = content['group_id'][0]
        device_id = content['device_id'][0]
    except:
        return json({'status': 'Warning', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition1 = "id='{}'".format(group_id)
    condition2 = "id='{}'".format(device_id)
    condition3 = "group_id='{}'".format(group_id)
    if len(my.my_scan(BASE, COLUMNS_BASE[0], condition2)) and len(
            my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[0], condition1)) == 0:
        return json({'status': 'Warning', 'info': 'no such a device or group'}, status=400)
    if device_id in tuple(*zip(*my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[1], condition3))):
        return json({'status': 'Warning', 'info': 'such a relationship already exists'}, status=400)
    try:
        columns = ','.join(COLUMNS_GROUP_DEVICE)
        values = ','.join([group_id, device_id])
        my.my_add(GROUP_DEVICE, columns, values)
        num = my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[5], condition=condition1)
        num = tuple(*zip(*num))[0]
        num = str(int(num) + 1)
        my.my_update(GROUP_INFO, COLUMNS_GROUP_INFO[5:], [num], condition1)
        my.commit()
        logger.info('add a new relation successfully')
        return json({'status': 'Done', 'info': 'relation has been added successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to add the relation because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


@app.post('/group_del_device')
async def group_del_device(request):
    content = request.json
    try:
        device_id = content['device_id'][0]
        group_id = content['group_id'][0]
    except:
        return json({'status': 'Warning', 'info': 'invalid input'}, status=400)

    condition = "device_id='{}' and group_id='{}'".format(device_id, group_id)
    my = MySQL()
    if len(my.my_scan(GROUP_DEVICE, condition=condition)) == 0:
        return json({'status': 'Warning', 'info': 'no such a relation'})
    try:
        my.my_delete(GROUP_DEVICE, condition)
        condition = "id='{}'".format(group_id)
        num = my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[5], condition=condition)
        num = tuple(*zip(*num))[0]
        num = str(int(num) - 1)
        my.my_update(GROUP_INFO, COLUMNS_GROUP_INFO[5:], [num], condition)
        my.commit()
        logger.info('delete the relation successfully')
        return json({'status': 'Done', 'info': 'delete the relation successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to delete the relation because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


@app.post('/group_scan_device')
async def group_scan_device(request):
    content = request.form
    try:
        group_id = content['group_id'][0]
    except:
        return json({'status': 'Warning', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition = "id='{}'".format(group_id)
    if len(my.my_scan(GROUP_INFO, condition=condition)) == 0:
        return json({'status': 'Warning', 'info': 'no such a group exists'})
    try:
        condition = "group_id='{}'".format(group_id)
        device_ids = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[1], condition)
        device_ids = tuple(*zip(*device_ids))
        devices = dict()
        for device_id in device_ids:
            condition = "id='{}'".format(device_id)
            info = my.my_scan(BASE, condition=condition)[0]
            number = 'device_{}'.format(str(device_ids.index(device_id) + 1))
            devices[number] = {'device_id': device_id, 'base': {'name': info[1],
                                                                'description': info[2], 'time_create': str(info[3]),
                                                                'time_update': str(info[4])}}
        logger.info('return info of devices belonging to a same group successfully')
        return json({'status': 'Done', 'info': {'group_id': group_id, 'including_devices': devices}})
    except Exception as e:
        logger.info('\033[0;31mError, fail to return devices belonging to a group because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


@app.post('/device_scan_group')
async def device_scan_group(request):
    content = request.form
    try:
        device_id = content['device_id'][0]
    except:
        return json({'status': 'Warning', 'info': 'invalid input'}, status=400)
    my = MySQL()
    condition = 'id=\'{}\''.format(device_id)
    if len(my.my_scan(BASE, condition=condition)) == 0:
        return json({'status': 'Waring', 'info': 'no such a device exists'})
    try:
        condition = 'device_id=\'{}\''.format(device_id)
        group_ids = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[0], condition)
        group_ids = tuple(*zip(*group_ids))
        groups = dict()
        for group_id in group_ids:
            condition = "id='{}'".format(group_id)
            info = my.my_scan(GROUP_INFO, condition=condition)[0]
            number = "group_{}".format(str(group_ids.index(group_id) + 1))
            groups[number] = {'group_id': group_id, 'name': info[1], 'description': info[2],
                              'time_create': str(info[3]),
                              'time_update': str(info[4]), 'device_num': info[5]}
        logger.info('return info of groups containing a same device successfully')
        return json({'status': 'Done', 'info': {'device_id': device_id, 'groups': groups}})
    except Exception as e:
        logger.info(
            '\033[0;31mError, fail to return groups containing a target device because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


@app.post('/device_del_group')
async def device_del_group(request):
    content = request.form
    try:
        device_id = content['device_id'][0]
    except:
        return json({'status': 'Warning', 'info': 'invalid input'}, status=400)
    condition = "id='{}'".format(device_id)
    my = MySQL()
    if len(my.my_scan(BASE, condition=condition)) == 0:
        return json({'status': 'Waring', 'info': 'no such a device exists'})
    try:
        condition = "device_id='{}'".format(device_id)
        group_ids = my.my_scan(GROUP_DEVICE, COLUMNS_GROUP_DEVICE[0], condition)
        group_ids = tuple(*zip(*group_ids))
        for group_id in group_ids:
            condition = "id='{}'".format(group_id)
            num = my.my_scan(GROUP_INFO, COLUMNS_GROUP_INFO[5], condition)
            num = tuple(*zip(*num))[0]
            num = str(int(num) - 1)
            my.my_update(GROUP_INFO, COLUMNS_GROUP_INFO[5:], [num], condition)
        condition = "device_id='{}'".format(device_id)
        my.my_delete(GROUP_DEVICE, condition)
        my.commit()
        logger.info('delete device from its groups successfully')
        return json({'status': 'Done', 'info': 'delete device from its groups successfully'})
    except Exception as e:
        my.roll_back()
        logger.info('\033[0;31mError, fail to delete device from its groups because: {}\033[0m'.format(str(e)))
        return json({'status': 'Error', 'info': 'please try again'})


if __name__ == '__main__':
    app.run('0.0.0.0', 8888, ssl=context)
