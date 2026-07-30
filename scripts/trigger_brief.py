"""Cron entrypoint (morning-brief service): triggers brief generation on the
running web service over Railway's private network, rather than touching the
SQLite file directly — Railway volumes can only attach to one service."""

import os
import urllib.request

host = os.environ["WEB_HOST"]
port = os.environ["WEB_PORT"]
token = os.environ["ADMIN_TOKEN"]

req = urllib.request.Request(
    f"http://{host}:{port}/api/brief/generate",
    method="POST",
    headers={"Authorization": f"Bearer {token}"},
)

with urllib.request.urlopen(req, timeout=60) as resp:
    print(resp.status, resp.read().decode())
