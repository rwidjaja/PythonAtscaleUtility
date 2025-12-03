import requests
import urllib3
import xml.etree.ElementTree as ET
import pandas as pd

# Disable TLS warnings (equivalent to curl --insecure)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Step 1: Authenticate and get JWT
auth_url = "https://ubuntu-atscale.atscaledomain.com:10500/default/auth"
resp = requests.get(auth_url, auth=("admin", "password"), verify=False)

if resp.status_code != 200:
    raise Exception(f"Auth failed: {resp.status_code} {resp.text}")

jwt = resp.text.strip()
headers = {"Authorization": f"Bearer {jwt}"}

# Step 2: Submit query
query_url = "https://ubuntu-atscale.atscaledomain.com:10502/query/orgId/default/submit"
payload = {
    "language": "SQL",
    "query": """SELECT `Internet Sales Cube`.d_city AS d_city, SUM(Salesamount1)
                FROM `Internet Sales Cube - Postgres` `Internet Sales Cube`
                GROUP BY 1""",
    "context": {
        "organization": {"id": "default"},
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

resp = requests.post(query_url, json=payload, headers=headers, verify=False)

if resp.status_code != 200:
    raise Exception(f"Query submit failed: {resp.status_code} {resp.text}")

# Step 3: Parse XML results
root = ET.fromstring(resp.text)

# Extract column names from metadata
columns = [col.find("name").text for col in root.findall(".//columns/column")]

# Extract rows
rows = []
for row in root.findall(".//data/row"):
    values = []
    for col in row.findall("column"):
        if "null" in col.attrib:  # handle null="true"
            values.append(None)
        else:
            values.append(col.text)
    rows.append(values)

# Step 4: Load into Pandas DataFrame
df = pd.DataFrame(rows, columns=columns)

# Convert numeric columns to floats where possible
for col in df.columns[1:]:  # skip d_city
    df[col] = pd.to_numeric(df[col], errors="coerce")

print(df.head(20))  # show first 20 rows
