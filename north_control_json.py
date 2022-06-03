import requests
import json
# the domain name
ADDRESS = 'http://localhost:8888'
# urls in the domain name
TARGET = ['/device_new', '/device_del', '/device_scan', '/device_update', '/scan_all_device', '/device_id_group',
          '/scan_all_device_group', '/group_new', '/group_del', '/group_scan', '/group_update', '/scan_all_group',
          '/group_new_device', '/group_del_device', '/group_scan_device', '/device_scan_group', '/device_del_group']
# in the following functions, the 'on' means 'basing on'
# 'A_to_B' means 'the situation A contains B'
def register_new_device(name: str, description='', hard_number='', hard_type='', efi_mac='', wifi_mac='', lte=''):
    address = ADDRESS+TARGET[0]

    with open('device.json') as f:
        content = json.load(f)
    content['base']['name'] = name
    content['base']['description'] = description
    content['hardware']['hard_number'] = hard_number
    content['hardware']['hard_type'] = hard_type
    content['hardware']['efi_mac'] = efi_mac
    content['hardware']['wifi_mac'] = wifi_mac
    content['hardware']['lte'] = lte
    content = json.dumps(content)
    response = requests.post(address, data=content)
    print(response.json())


def delete_device_on_device_id(device_id: str):
    address = ADDRESS+TARGET[1]

    with open('device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data = json.dumps(data)
    response = requests.post(address, data=data)
    print(response.json())


def get_device_info_on_device_id(device_id: str):
    address = ADDRESS + TARGET[2]

    with open('device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def update_device_on_device_id(device_id: str, name='', description='', hard_number='', hard_type='', efi_mac='',
                               wifi_mac='', lte='', base_version='', base_status='good', service_version='',
                               service_status='good'):
    address = ADDRESS + TARGET[3]
    with open('device.json') as f:
        data = json.load(f)

    data['device_id'] = device_id
    data['name'] = name
    data['description'] = description
    data['hard_number'] = hard_number
    data['hard_type'] = hard_type
    data['efi_mac'] = efi_mac
    data['wifi_mac'] = wifi_mac
    data['lte'] = lte
    data['base_version'] = base_version
    data['base_status'] = base_status
    data['service_version'] = service_version
    data['service_status'] = service_status
    data = json.dumps(data)
    response = requests.post(address, data=data)
    print(response.json())


def get_all_device_info():
    address = ADDRESS + TARGET[4]
    response = requests.get(address)
    print(response.json())


def get_device_group_on_device_id(device_id: str):
    address = ADDRESS + TARGET[5]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def get_all_device_include_group_info():
    address = ADDRESS + TARGET[6]
    response = requests.get(address)
    print(response.json())


def register_new_group(name: str, description=''):
    address = ADDRESS + TARGET[7]
    with open('group.json') as f:
        data = json.load(f)
    data['name'] = name
    data['description'] = description
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def delete_group_on_group_id(group_id: str):
    address = ADDRESS + TARGET[8]
    with open('group.json') as f:
        data = json.load(f)
    data['group_id'] = group_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def get_group_info_on_group_id(group_id: str):
    address = ADDRESS + TARGET[9]
    with open('group.json') as f:
        data = json.load(f)
    data['group_id'] = group_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def update_group_on_group_id(group_id: str, name='', description=''):
    address = ADDRESS + TARGET[10]
    with open('group.json') as f:
        data = json.load(f)
    data['group_id'] = group_id
    data['name'] = name
    data['description'] = description
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def get_all_device_grouping_info():
    address = ADDRESS + TARGET[11]
    response = requests.get(address)
    print(response.json())


def add_device_to_group(device_id: str, group_id: str):
    address = ADDRESS + TARGET[12]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data['group_id'] = group_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def delete_device_from_group(device_id: str, group_id: str):
    address = ADDRESS + TARGET[13]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data['group_id'] = group_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def get_all_devices_on_group_id(group_id: str):
    address = ADDRESS + TARGET[14]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['group_id'] = group_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def get_all_groups_on_device_id(device_id: str):
    address = ADDRESS + TARGET[15]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


def delete_all_grouping_on_device_id(device_id: str):
    address = ADDRESS + TARGET[16]
    with open('group_and_device.json') as f:
        data = json.load(f)
    data['device_id'] = device_id
    data = json.dumps(data)
    response = requests.post(address, data)
    print(response.json())


if __name__ == '__main__':
    # requests.get('https://baidu.com')
    delete_device_on_device_id('4626739495335624705')
    register_new_device('test passwd')
    # register_new_group('test group 11')
    # delete_group_on_group_id('4626646619519975425')
    # get_group_info_on_group_id('4626648221832183809')
    # update_group_on_group_id('4626648221832183809', 'mymymy', 'test this function')
    # add_device_to_group('4626438592640581633', '4626460505890881537')
    # delete_device_from_group('4626438592640581633', '4626460505890881537')
    # get_all_device_include_group_info()
    # get_all_device_grouping_info()
    # get_group_info_on_group_id('4626460505890881537')
    # get_all_devices_on_group_id('4626460505890881537')
    # get_all_groups_on_device_id('4626438592640581633')
    # delete_all_grouping_on_device_id('4626438592640581633')
    pass
