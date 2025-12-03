import json
import requests
import urllib3
import xml.etree.ElementTree as ET
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config.json
with open("config.json") as f:
    cfg = json.load(f)

instance_type = cfg["instance_type"]
username = cfg["username"]
password = cfg["password"]
host = cfg["host"]
organization = cfg.get("organization", "default")
client_id = cfg.get("client_id")
client_secret = cfg.get("client_secret")

def get_jwt_installer(host, user, password):
    url = f"https://{host}:10500/default/auth"
    resp = requests.get(url, auth=(user, password), verify=False)
    resp.raise_for_status()
    return resp.text.strip()

def get_jwt_container(host, user, password, client_id, client_secret):
    url = f"https://{host}/auth/realms/atscale/protocol/openid-connect/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "username": user,
        "password": password,
        "grant_type": "password"
    }
    resp = requests.post(url, data=data, verify=False)
    resp.raise_for_status()
    return resp.json()["access_token"]

def submit_query(host, jwt, payload, installer=True):
    if installer:
        url = f"https://{host}:10502/query/orgId/{organization}/submit"
    else:
        url = f"https://{host}/engine/query/submit"
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.text

def parse_xml_results(xml_text):
    root = ET.fromstring(xml_text)
    columns = [col.find("name").text for col in root.findall(".//columns/column")]
    rows = []
    for row in root.findall(".//data/row"):
        values = []
        for col in row.findall("column"):
            if "null" in col.attrib:
                values.append(None)
            else:
                values.append(col.text)
        rows.append(values)
    df = pd.DataFrame(rows, columns=columns)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# Example query payload
payload = {
    "language": "SQL",
    "query": """SELECT `Internet Sales Cube`.d_city AS d_city, SUM(Salesamount1)
                FROM `Internet Sales Cube` `Internet Sales Cube`
                GROUP BY 1""",
    "context": {
        "organization": {"id": organization},
        "environment": {"id": "default"},
        "project": {"name": "Sales Insights - Postgres"}
    },
    "useAggs": True,
    "genAggs": True,
    "fakeResults": False,
    "dryRun": False,
    "useLocalCache": True,
    "useAggregateCache": True,
    "timeout": "2.minutes"
}

# Runtime
if instance_type == "installer":
    jwt = get_jwt_installer(host, username, password)
    xml_text = submit_query(host, jwt, payload, installer=True)
else:
    jwt = get_jwt_container(host, username, password, client_id, client_secret)
    xml_text = submit_query(host, jwt, payload, installer=False)

df = parse_xml_results(xml_text)
print(df.head(20))
