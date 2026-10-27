#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error
import ssl

def main():
    if len(sys.argv) < 2:
        print("Usage: disable_port.py <device_id>")
        sys.exit(1)
    device = sys.argv[1]
    base = "https://10.15.235.116"
    username = "admin"
    password = ""
    context = ssl._create_unverified_context()
    # 1. Login
    login_url = f"{base}/api/v1/Session"
    data = json.dumps({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, context=context, timeout=10)
    except urllib.error.URLError as e:
        print(f"Login failed: {e}")
        sys.exit(1)
    login_data = json.load(resp)
    session = login_data.get('session')
    if not session:
        print("No session in response")
        sys.exit(1)
    # 2. Disable
    disable_url = f"{base}/api/v1/devices/table/{device}/disable"
    req = urllib.request.Request(disable_url, headers={'ticket': session}, method='PUT')
    try:
        resp = urllib.request.urlopen(req, context=context, timeout=10)
        print(f"Disable {device}: {resp.status} {resp.reason}")
    except urllib.error.HTTPError as e:
        print(f"Disable {device} failed: {e.code} {e.reason}")
        # read body
        try:
            body = e.read().decode()
            print(f"Response: {body}")
        except:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Disable {device} URL error: {e}")
        sys.exit(1)
    # 3. Logout (optional)
    logout_url = f"{base}/api/v1/Session"
    req = urllib.request.Request(logout_url, headers={'ticket': session}, method='DELETE')
    try:
        urllib.request.urlopen(req, context=context, timeout=10)
    except Exception:
        pass  # ignore
    print(f"Success: {device} disabled")

if __name__ == "__main__":
    main()
