# Antminer Power Control with Shelly 3EM

This project automates power control for an Antminer using real-time power readings from a Shelly 3EM and a Shelly 1PM switch. The script dynamically adjusts the miner's power consumption to stay within defined limits.

## Features

- Monitors power consumption using the Shelly 3EM.
- Checks if the Antminer is powered on via the Shelly 1PM.
- Retrieves and maintains an authentication token for Antminer API calls.
- Reads the Antminer's tuner state to determine current power settings.
- Adjusts power dynamically while respecting minimum and maximum limits.
- Ensures the Antminer has sufficient time to boot before making adjustments.

## Hardware Requirements

- **Antminer** running Braiins OS with gRPC support.
- **Shelly 3EM** for real-time power monitoring.
- **Shelly 1PM** for switching the Antminer on/off.
- **Raspberry Pi 4** (or another Linux device) for running the script.

## Installation

1. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   pip install requests
   ```
2. Install `grpcurl` (if not already installed):
   ```bash
   sudo apt install grpcurl
   ```
3. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/yourusername/antminer-power-control.git
   cd antminer-power-control
   ```
4. Update the configuration values in `control_antminer_with_shelly.py`:
   - **Shelly 3EM & Shelly 1PM IP addresses**
   - **Antminer IP address and credentials**
   - **Power limits and adjustment step size**

## Usage

Run the script using:

```bash
python3 control_antminer_with_shelly.py
```

## Configuration Parameters

- **Power Limits:**
  - `MAX_POWER_LIMIT`: Maximum power Antminer can use (default: 2800W).
  - `MIN_POWER_LIMIT`: Minimum power to avoid shutdown (default: 900W).
- **Power Adjustment:**
  - `POWER_ADJUSTMENT_WATT`: Step size for power adjustments (default: 250W).
- **Timing:**
  - `boot_wait_time`: Time to wait after switching on Antminer (default: 5 min).

## How It Works

1. Checks if the Antminer is powered on via Shelly 1PM.
2. If powered on, waits 5 minutes for boot-up.
3. Retrieves a new authentication token for Antminer.
4. Reads the current power consumption from Shelly 3EM.
5. Fetches the Antminer tuner state to determine power settings.
6. If power consumption is too high/low, adjusts Antminer power accordingly.
7. Repeats the process every 5 minutes.

## Logs & Debugging

The script prints real-time updates:

```
Shelly Switch: ON  
Shelly Power: Actual -1726.302 W | Average -1676.58 W  
Tuner State:  
  Current Target: 2000 W  
  Estimated Power Consumption: 2038 W  
  Target Power: 2000 W  
Power adjustments allowed within limits  
Antminer Adjustment (Increase): {"powerTarget": {"watt": "2250"}}  
```

## Future Improvements

- Add error handling for unstable network connections.
- Implement logging to a file for long-term tracking.
- Create a web dashboard for monitoring power consumption.
