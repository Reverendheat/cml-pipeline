import os
from dotenv import load_dotenv
load_dotenv()

config_ios_payload = f"""
hostname HQ-RTR
interface gig0/0
ip add dhcp
desc to ISP
ip nat outside
no shut
int gig0/1
ip add 172.16.20.254 255.255.255.0
desc inside interface
ip nat inside
no shut
ip route 0.0.0.0 0.0.0.0 gig0/0
ip domain name parakoopa.local
crypto key generate rsa modulus 2048
ip ssh version 2
line vty 0 15
login local
transport input ssh
username {os.getenv('IOS_USERNAME')} privilege 15 password 0 {os.getenv('IOS_PASSWORD')}
ip dhcp pool TestPool
network 172.16.20.0 /24
default-router 172.16.20.254
dns-server 8.8.8.8
access-list 1 permit 172.16.20.0 0.0.0.255
ip nat inside source list 1 interface gig0/0 overload
ip nat inside source static tcp 172.16.20.1 22 interface gig0/0 8022
"""

config_ec_payload = "bridge0"
