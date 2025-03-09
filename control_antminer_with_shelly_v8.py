import requests
import time
import subprocess
import json
from collections import deque

# The IP addresses of your Shelly devices
SHELLY_POWER_IP = "http://192.168.178.70/rpc/EM.GetStatus?id=0"
SHELLY_SWITCH_IP = "http://192.168.178.65/rpc/Switch.GetStatus?id=0"
VALUE_HISTORY = deque(maxlen=5)  # Store the last 5 power readings

# Antminer Configuration
GRPCURL_PATH = "/home/pi/grpcurl"
GRPC_SERVER = "192.168.178.96:50051"
AUTH_SERVICE = "braiins.bos.v1.AuthenticationService/Login"
INCREASE_SERVICE = "braiins.bos.v1.PerformanceService.IncrementPowerTarget"
DECREASE_SERVICE = "braiins.bos.v1.PerformanceService.DecrementPowerTarget"
SET_POWER_SERVICE = "braiins.bos.v1.PerformanceService.SetPowerTarget"
TUNER_STATE_SERVICE = "braiins.bos.v1.PerformanceService/GetTunerState"
USERNAME = "root"
PASSWORD = "root"
POWER_ADJUSTMENT_WATT = 250
MAX_POWER_LIMIT = 2800
MIN_POWER_LIMIT = 900
DEFAULT_POWER_TARGET = 900
POWER_THRESHOLD = 300

# Store the authentication token
auth_token = None
current_target = None

def get_auth_token():
    """Retrieves an authentication token for Antminer."""
    global auth_token
    
    command = [
        GRPCURL_PATH, "-plaintext", "-d",
        f'{{"username": "{USERNAME}", "password": "{PASSWORD}"}}',
        GRPC_SERVER, AUTH_SERVICE
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        try:
            response_json = json.loads(result.stdout)
            auth_token = response_json.get("token")
            print("New authentication token retrieved.")
        except json.JSONDecodeError:
            print("Error decoding authentication response.")
            auth_token = None
    else:
        print("Failed to retrieve authentication token.")
        auth_token = None

def get_actual_power():
    """Fetches the actual power consumption from the Shelly device."""
    try:
        response = requests.get(SHELLY_POWER_IP)
        if response.status_code == 200:
            data = response.json()
            actual_power = data.get("total_act_power")
            if actual_power is not None:
                VALUE_HISTORY.append(actual_power)
                average_power = sum(VALUE_HISTORY) / len(VALUE_HISTORY)
                print(f"Shelly Power: Actual {actual_power} W | Average {average_power:.2f} W")
                return average_power  # Use average power for decision making
            else:
                print("Key 'total_act_power' not found in the response.")
        else:
            print(f"Error fetching data: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return None

def get_tuner_state():
    """Fetches and displays the tuner state."""
    global auth_token, current_target
    command = [
        GRPCURL_PATH, "-plaintext", "-H", f"Authorization: {auth_token}",
        GRPC_SERVER, TUNER_STATE_SERVICE
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        try:
            tuner_data = json.loads(result.stdout)
            current_target = int(tuner_data.get("powerTargetModeState", {}).get("currentTarget", {}).get("watt", DEFAULT_POWER_TARGET))
            estimated_power = tuner_data.get("powerTargetModeState", {}).get("profile", {}).get("estimatedPowerConsumption", {}).get("watt", "N/A")
            target_power = tuner_data.get("powerTargetModeState", {}).get("profile", {}).get("target", {}).get("watt", "N/A")
            
            print("Tuner State:")
            print(f"  Current Target: {current_target} W")
            print(f"  Estimated Power Consumption: {estimated_power} W")
            print(f"  Target Power: {target_power} W")
        except json.JSONDecodeError:
            print("Error decoding tuner state response.")
    else:
        print("Error fetching tuner state:", result.stderr)

def adjust_antminer_power(amount, increase=True):
    """Increases or decreases Antminer power based on amount."""
    global auth_token
    if not auth_token:
        print("Skipping power adjustment due to missing token.")
        return
    
    service = INCREASE_SERVICE if increase else DECREASE_SERVICE
    action_key = "power_target_increment" if increase else "power_target_decrement"
    
    command = [
        GRPCURL_PATH, "-plaintext",
        "-H", f"Authorization: {auth_token}",
        "-d", f'{{"save_action": "SAVE_ACTION_SAVE_AND_APPLY", "{action_key}": {{"watt": {amount}}}}}',
        GRPC_SERVER, service
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Antminer Adjustment ({'Increase' if increase else 'Decrease'}): {result.stdout}")
    if result.stderr:
        print("Error:", result.stderr)

def check_shelly_switch():
    """Checks whether the Shelly device output is ON or OFF."""
    try:
        response = requests.get(SHELLY_SWITCH_IP)
        if response.status_code == 200:
            data = response.json()
            switch_status = data.get("output", False)
            print(f"Shelly Switch: {'ON' if switch_status else 'OFF'}")
            return switch_status
        else:
            print(f"Error fetching switch status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return False

if __name__ == "__main__":
    boot_wait_time = 300  # Default boot wait time of 5 minutes
    antminer_was_off = True  # Track if Antminer was previously off
    
    while True:
        shelly_on = check_shelly_switch()
        
        if shelly_on:
            if antminer_was_off:
                boot_wait_time = 300  # Give Antminer 5 minutes to boot up
                get_auth_token()
                antminer_was_off = False
            
            actual_power = get_actual_power()
            get_tuner_state()
            
            if current_target is not None:
                if actual_power < -POWER_THRESHOLD and current_target + POWER_ADJUSTMENT_WATT <= MAX_POWER_LIMIT:
                    adjust_antminer_power(POWER_ADJUSTMENT_WATT, increase=True)
                elif actual_power > POWER_THRESHOLD and current_target - POWER_ADJUSTMENT_WATT >= MIN_POWER_LIMIT:
                    adjust_antminer_power(POWER_ADJUSTMENT_WATT, increase=False)
        else:
            antminer_was_off = True
        
        time.sleep(boot_wait_time if antminer_was_off else 300)
