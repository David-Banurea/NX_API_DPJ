from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# URL dan kredensial server NX-API
NXAPI_URL = "https://sbx-nxos-mgmt.cisco.com:443/ins"  # URL Sandbox NX-API
NXAPI_HEADERS = {
    "Content-Type": "application/json",
}
NXAPI_AUTH = ("admin", "Admin_1234!")  # Kredensial sandbox

# Fungsi untuk Show Interfaces
def get_interfaces():
    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": "show interface brief",
            "output_format": "json"
        }
    }
    try:
        response = requests.post(
            NXAPI_URL,
            json=payload,
            headers=NXAPI_HEADERS,
            auth=NXAPI_AUTH,
            verify=False
        )
        response.raise_for_status()  # Error jika status kode bukan 200
        file_data = response.json()

        # Debug respons JSON lengkap
        print("NX-API Full Response:", file_data)

        # Parsing data interfaces
        interfaces = file_data.get("ins_api", {}).get("outputs", {}).get("output", {}).get("body", {}).get("TABLE_interface", {}).get("ROW_interface", [])

        # Jika hanya satu interface (bentuk dictionary), ubah menjadi list
        if isinstance(interfaces, dict):
            interfaces = [interfaces]

        # Debug data yang diproses
        print("Parsed Interfaces:", interfaces)
        return interfaces

    except requests.exceptions.RequestException as e:
        print(f"Error fetching interfaces from NX-API: {e}")
        return []

# Fungsi untuk Show Device Info
def get_device_info():
    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": "show version",
            "output_format": "json"
        }
    }
    try:
        response = requests.post(
            NXAPI_URL,
            json=payload,
            headers=NXAPI_HEADERS,
            auth=NXAPI_AUTH,
            verify=False  # Abaikan SSL
        )
        response.raise_for_status()
        file_data = response.json()
        print("Device Info Response:", file_data)  # Debug untuk perangkat
        return file_data.get("ins_api", {}).get("outputs", {}).get("output", {}).get("body", {})

    except requests.exceptions.RequestException as e:
        print(f"Error fetching device info from NX-API: {e}")
        return {}

# Fungsi untuk Non-VLAN Interfaces
def get_non_vlan_interfaces():
    interfaces = get_interfaces()
    return [intf for intf in interfaces if "VLAN" not in intf.get("interface", "").upper()]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/navigate', methods=['POST'])
def navigate():
    command = request.form.get('command')
    if command == 'show_interfaces':
        return redirect(url_for('interfaces'))
    elif command == 'interface_detail':
        return redirect(url_for('interface_detail'))
    elif command == 'device_info':
        return redirect(url_for('device_info'))
    elif command == 'non_vlan_interfaces':
        return redirect(url_for('non_vlan'))
    else:
        return "Invalid Command", 400

@app.route('/interfaces')
def interfaces():
    data = get_interfaces()  # Ambil data dari NX-API
    print("Data sent to interfaces.html:", data)  # Debug untuk memastikan data diteruskan
    return render_template('interfaces.html', interfaces=data)

@app.route('/interface_detail', methods=['GET', 'POST'])
def interface_detail():
    interfaces = get_interfaces()
    detail = None
    error = None

    if request.method == 'POST':
        interface_name = request.form.get('interface_name')
        detail = next((intf for intf in interfaces if intf["interface"] == interface_name), None)
        if not detail:
            error = f"Interface '{interface_name}' not found. Please try again."

    return render_template('interface_detail.html', interfaces=interfaces, detail=detail, error=error)

@app.route('/device_info')
def device_info():
    data = get_device_info()
    print("Data sent to device_info.html:", data)  # Debug untuk perangkat
    return render_template('device_info.html', info=data)

@app.route('/non_vlan')
def non_vlan():
    data = get_non_vlan_interfaces()
    print("Data sent to non_vlan.html:", data)  # Debug untuk non-VLAN interfaces
    return render_template('non_vlan.html', interfaces=data)

if __name__ == '__main__':
    app.run(debug=True)