from dotenv import load_dotenv
import json
import requests
import os
import sys
import time
from netmiko import ConnectHandler
from config import config_ios_payload, config_ec_payload
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def main():
    # Settings the base api URL for CML
    base_url = f"{os.getenv('CML_SERVER')}/api/v0/"

    # Log into CML
    login_payload = {
        "username": os.getenv("CML_USERNAME"),
        "password": os.getenv("CML_PASSWORD")
    }
    login_response = requests.post(
        url=f"{base_url}/authenticate", data=json.dumps(login_payload), verify=False).json()
    headers = {
        "Authorization": f"Bearer {login_response}"
    }

    # Create a Lab
    lab_title = "para_pipeline_test"
    lab_response = requests.post(
        url=f"{base_url}/labs?title={lab_title}", headers=headers, verify=False).json()
    lab_id = lab_response['id']

    # Add Nodes to Lab
    nodes = [
        {
            "x": 50,
            "y": 0,
            "label": "ISP_External",
            "node_definition": "external_connector"
        },
        {
            "x": 50,
            "y": 0,
            "label": "HQ_RTR",
            "node_definition": "iosv"
        },
        {
            "x": 50,
            "y": 0,
            "label": "HQ_SWITCH",
            "node_definition": "iosvl2"
        },
        {
            "x": 50,
            "y": 0,
            "label": "HQ_SERVER",
            "node_definition": "alpine"
        },
    ]

    # Iterate over the nodes, and create
    for node in nodes:
        i = 0
        node['y'] += i
        node_response = requests.post(url=f"{base_url}/labs/{lab_id}/nodes?populate_interfaces=true", data=json.dumps(
            node), headers=headers, verify=False).json()
        i += 200
        node['id'] = node_response['id']
        # Get the interfaces assigned to the nodes
        node_interface_response = requests.get(
            url=f"{base_url}/labs/{lab_id}/nodes/{node['id']}/interfaces", headers=headers, verify=False).json()
        node['interfaces'] = node_interface_response
        # Link the two devices together
        if "interfaces" in nodes[0] and "interfaces" in nodes[1] and "interfaces" in nodes[2] and "interfaces" in nodes[3]:
            # Connect ISP and HQRTR
            link_payload = {
                "src_int": nodes[0]['interfaces'][0],
                "dst_int": nodes[1]['interfaces'][1]
            }
            link_response = requests.post(
                url=f"{base_url}/labs/{lab_id}/links", data=json.dumps(link_payload), headers=headers, verify=False).json()
            # Connect HQRTR and HQSWITCH
            link_payload = {
                "src_int": nodes[1]['interfaces'][2],
                "dst_int": nodes[2]['interfaces'][1]
            }
            link_response = requests.post(
                url=f"{base_url}/labs/{lab_id}/links", data=json.dumps(link_payload), headers=headers, verify=False).json()
            # Connect HQSWITCH and HQSERVER
            link_payload = {
                "src_int": nodes[2]['interfaces'][2],
                "dst_int": nodes[3]['interfaces'][0]
            }
            link_response = requests.post(
                url=f"{base_url}/labs/{lab_id}/links", data=json.dumps(link_payload), headers=headers, verify=False).json()

    # Put a config on the IOS Router
    config_ios_put_response = requests.put(
        url=f"{base_url}/labs/{lab_id}/nodes/{nodes[1]['id']}/config", data=config_ios_payload, headers=headers, verify=False).json()
    config_ec_put_response = requests.put(
        url=f"{base_url}/labs/{lab_id}/nodes/{nodes[0]['id']}/config", data=config_ec_payload, headers=headers, verify=False).json()

    # Start the lab
    print("Starting Lab...")
    start_response = requests.put(
        url=f"{base_url}/labs/{lab_id}/start", headers=headers, verify=False).json()

    # Get the L3 address assigned from DHCP
    # TODO: Need to make it so this can fail gracefully
    ios_ipv4 = ''
    timeout = 0
    while ios_ipv4 == '':
        if timeout > 600:
            sys.exit("Timeout exceeded for getting DHCP address")
        print(f'checking for ipv4 address...{timeout} seconds elapsed...')
        timeout += 10
        time.sleep(10)
        l3_response = requests.get(
            url=f"{base_url}/labs/{lab_id}/nodes/{nodes[1]['id']}/layer3_addresses", headers=headers, verify=False).json()
        for k1, v1 in l3_response['interfaces'].items():
            for k2, v2 in v1.items():
                if k2 == "ip4":
                    if v2:
                        ios_ipv4 = v2[0]
                        print(f"Assigned : {ios_ipv4}")

    # Test internet connectivity from HQRTR
    print("Waiting 15 seconds, then ping tests to 8.8.8.8 from HQRTR")
    time.sleep(15)
    iosv = {
        'device_type': 'cisco_ios',
        'host': ios_ipv4,
        "username": os.getenv('IOS_USERNAME'),
        "password": os.getenv('IOS_PASSWORD')
    }
    net_connect = ConnectHandler(**iosv)
    ping_output = net_connect.send_command('ping 8.8.8.8')
    if "(0/5)" in ping_output:
        print("Ping test: Failed")
    else:
        print("Ping test from router to ISP: Success")

    # Test internet connectivity from HQSERVER
    print("Waiting 15 seconds, then ping tests to 8.8.8.8 from HQSERVER")
    time.sleep(15)
    alpine = {
        'device_type': 'linux',
        'host': ios_ipv4,
        "username": os.getenv('ALPINE_USERNAME'),
        "password": os.getenv('ALPINE_PASSWORD'),
        "port": 8022
    }
    net_connect = ConnectHandler(**alpine)
    ping_output = net_connect.send_command('ping 8.8.8.8')
    print(ping_output)

    # Finally stop, wipe, and delete the lab.
    lab_stop_response = requests.put(
        url=f"{base_url}/labs/{lab_id}/stop", headers=headers, verify=False).json()
    lab_wipe_response = requests.put(
        url=f"{base_url}/labs/{lab_id}/wipe", headers=headers, verify=False).json()
    lab_delete_response = requests.delete(
        url=f"{base_url}/labs/{lab_id}", headers=headers, verify=False).json()

    print(f"Stopped: {lab_stop_response}")
    print(f"Wiped: {lab_wipe_response}")
    print(f"Deleted: {lab_delete_response}")


if __name__ == "__main__":
    main()
