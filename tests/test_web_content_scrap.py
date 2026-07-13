import os
import httpx

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)

os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12'

import streamlit as st

username = st.secrets["brain"]["username"]
password = st.secrets["brain"]["password"]
auth = (username, password)

client = httpx.Client(
    follow_redirects=False,
    timeout=30,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
)

r = client.post("https://api.worldquantbrain.com/authentication", auth=auth)
print("login:", r.status_code, r.url)

r = client.get(
    "https://api.worldquantbrain.com/authentication/support"
    "?return_to=https%3A%2F%2Fsupport.worldquantbrain.com%2Fhc%2Fen-us%2Fcommunity%2Ftopics"
)
print("support redirect:", r.status_code, r.headers.get("location"))

while r.status_code in (301, 302, 303, 307, 308):
    location = r.headers.get("location")
    if not location:
        break
    r = client.get(location)
    print("redirect:", r.status_code, r.url, r.headers.get("location"))

print(r.text[:5000])