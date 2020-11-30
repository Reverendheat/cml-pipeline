# CML-Pipeline

Collection of scripts/playbooks to explore Cisco Modeling Labs and its functionality.

Find Cisco Modeling Labs here: https://www.cisco.com/c/en/us/products/cloud-systems-management/modeling-labs/index.html

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install -r requirements.txt
```

.env file example

```bash
CML_SERVER=https://ip
CML_USERNAME=admin
CML_PASSWORD=password
IOS_USERNAME=cisco
IOS_PASSWORD=cisco
```

## lab_builds.py

Using requests/CML REST API, builds a 2 node lab with external connectivity (bridge mode), then tests internet access by pinging from iosv node to the internet.

## License

[MIT](https://choosealicense.com/licenses/mit/)
