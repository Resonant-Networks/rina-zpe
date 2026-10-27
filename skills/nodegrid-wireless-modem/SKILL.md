---
name: nodegrid-wireless-modem
description: Get ZPE Nodegrid wireless modem info via REST API.
---

# ZPE Nodegrid Wireless Modem Info

## Target
ZPE Nodegrid device at `https://10.15.235.116` with credentials `admin:<NODEGRID_PASSWORD>`

## Authentication
```
POST /api/v1/Session
{"username": "admin", "password": "<NODEGRID_PASSWORD>"}
→ {"session": "<ticket>"}
```
Use `ticket: <session>` header on all subsequent requests.

## Endpoints

### Get All Wireless Modems
```
GET /api/v1/tracking/devices/wirelessmodem
```
Returns JSON array with modem summary information.

### Get Specific Wireless Modem Detail
```
GET /api/v1/tracking/devices/wirelessmodem/{slot}|{interface}
```
Returns detailed JSON for a specific modem (e.g., `Channel-A|cdc-wdm0`).

## Example Script
```python
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NODEGRID_IP = "10.15.235.116"
BASE_URL = f"https://{NODEGRID_IP}/api/v1"
USERNAME = "admin"
PASSWORD = "<NODEGRID_PASSWORD>"

def auth():
    resp = requests.post(
        f"{BASE_URL}/Session",
        json={"username": USERNAME, "password": PASSWORD},
        verify=False, timeout=10
    )
    resp.raise_for_status()
    return resp.json()["session"]

def get_wireless_modems(ticket):
    resp = requests.get(
        f"{BASE_URL}/tracking/devices/wirelessmodem",
        headers={"ticket": ticket, "accept": "application/json"},
        verify=False, timeout=10
    )
    resp.raise_for_status()
    return resp.json()

def get_wireless_modem_detail(ticket, slot_interface):
    resp = requests.get(
        f"{BASE_URL}/tracking/devices/wirelessmodem/{slot_interface}",
        headers={"ticket": ticket, "accept": "application/json"},
        verify=False, timeout=10
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    ticket = auth()
    # Get summary
    modems = get_wireless_modems(ticket)
    print("\n📊 Wireless Modem Summary:")
    headers = ["Slot", "Interface", "Status", "SIM State", "Active", "Data Consumption",
               "Operator", "Radio Mode", "Signal Strength"]
    print("{:<12} {:<12} {:<12} {:<12} {:<10} {:<20} {:<12} {:<12} {:<15}".format(*headers))
    for dev in modems:
        print("{:<12} {:<12} {:<12} {:<12} {:<10} {:<20} {:<12} {:<12} {:<15}".format(
            dev.get("slot", ""),
            dev.get("interface", ""),
            dev.get("status", ""),
            dev.get("sim_state", ""),
            dev.get("active", ""),
            dev.get("data_consumption", ""),
            dev.get("operator", ""),
            dev.get("radio_mode", ""),
            dev.get("signal_strength", "")
        ))
    
    # Get detail for first modem if available
    if modems:
        first = modems[0]
        slot = first.get("slot")
        interface = first.get("interface")
        if slot and interface:
            detail = get_wireless_modem_detail(ticket, f"{slot}|{interface}")
            print_detail(detail)
    
    # cleanup
    requests.delete(f"{BASE_URL}/Session", headers={"ticket": ticket}, verify=False, timeout=10)

def print_detail(data):
    print("\n📡 Wireless Modem Details")
    print(""""
    Slot:           {slot}
    Interface:      {interface}
    Status:         {status}
    Modem Model:    {modem_model}
    Firmware:       {firmware_version}
    Hardware:       {hardware_version}
    Carrier Config: {carrier_configuration}
    Equipment ID:   {equipment_id}

    Operator:       {current_operator}
    IP Address:     {ip_address}
    Gateway:        {ip_gateway}
    DNS:            {ip_primary_dns}
    MTU:            {carrier_mtu}

    Allowed Modes:  {allowed_modes}
    Preferred Mode: {preferred_mode}
    Active SIM:     {active_sim_card}
    Temperature:    {temperature}°C

    📱 **SIM 1 Status:**
      State:        {sim_1_sim_state}
      Subscriber ID:{sim_1_subscriber_id}
      ICCID:        {sim_1_circuit_card_id}
      Operator:     {sim_1_operator}
      Phone:        {sim_1_phone_number_configured or '(not configured)'}
      APN:          {sim_1_access_point_name}
      Connection:   {sim_1_connection}
      Signal:       {sim_1_signal_strength}
      Bytes Used:   {bytes_accumulated_sim_1:,} ({bytes_accumulated_sim_1 / 1024 / 1024:.1f} MB)
      Last Update:  {sim_1_last_update}

    📱 **SIM 2 Status:**
      State:        {sim_2_sim_state}
      Bytes Used:   {bytes_accumulated_sim_2:,} ({bytes_accumulated_sim_2 / 1024 / 1024:.1f} MB)
      Last Update:  {sim_2_last_update or '(never)'}
    """.format(**data))
```

## Notes
- Use `verify=False` (self-signed cert)
- Session cleanup via DELETE /api/v1/Session
- The summary endpoint returns array of modems with basic stats
- The detail endpoint returns comprehensive SIM and connection info
- Data consumption shown in bytes (convert to MB/GB as needed)
- Signal strength includes technical details (RSSI, RSRQ, RSRP, SNR)
