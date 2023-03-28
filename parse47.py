import pprint
from xml.etree import ElementTree

import requests
import xmltodict

with open("xml/1a. Perform XCPD patient discovery.xml") as iti47:
    print("ITI38 query")
    print("-" * 20)
    dom = ElementTree.parse(iti47)
    root = dom.getroot()
    body = ElementTree.tostring(root)
    headers = {"Content-Type": "application/xml"}
    # url = "http://127.0.0.1:8000/SOAP/iti47"
    url = "http://0.0.0.0:80/SOAP/iti47"
    r = requests.post(url, data=body, headers=headers)
    print(r.status_code)
    print(r.text)
    print("-" * 20)

