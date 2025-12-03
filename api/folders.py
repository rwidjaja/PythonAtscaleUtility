import requests
import urllib3
from common import append_log

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_folders(host, org, jwt):
    url = f"https://{host}:10500/api/1.0/org/{org}/folders"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, verify=False, timeout=20)
    resp.raise_for_status()
    return resp.json()