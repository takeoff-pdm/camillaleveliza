import time
import json
from websocket import create_connection

from loudness_tracker import LoudnessTracker

# Websocket server configuration
CAMILLADSP_ADRESS = "ws://0.0.0.0:1234"

# Channel configuration
K_WEIGHTED_CHANNEL_NUMBER = 0   # The channel number that represents the K-weighted signal for loudness measurement
SUB_BASS_CHANNEL_NUMBER = 1     # The channel number that represents the sub-bass signal for breakdown detection

# Configuration Parameters
TARGET_LUFS = -14.0             # Perceived loudness setpoint
SILENCE_FLOOR_DB = -40.0        # Gate threshold to freeze gain on silence beneath target loudness
BREAKDOWN_SUB_DROP_DB = -10.0   # Dropping sub energy threshold for breakdown freeze

MAX_BOOST_DB = 6.0              # Hard safety ceiling
MAX_CUT_DB = -20.0              # Hard safety floor

# Time Constants (in seconds)
ATTACK_TIME_SEC = 8.0           # Time to glide volume down
RELEASE_TIME_SEC = 20.0         # Time to glide volume up
POLL_INTERVAL_SEC = 0.1         # Polling frequency
SHORT_WINDOW_SEC = 2.0          # Short-term loudness window
LONG_WINDOW_SEC = 20.0          # Long-term loudness window


ws = create_connection(CAMILLADSP_ADRESS)

lufs_tracker = LoudnessTracker(poll_interval_sec=POLL_INTERVAL_SEC, short_window_sec=SHORT_WINDOW_SEC, long_window_sec=LONG_WINDOW_SEC)
sub_bass_tracker = LoudnessTracker(poll_interval_sec=POLL_INTERVAL_SEC, short_window_sec=SHORT_WINDOW_SEC, long_window_sec=LONG_WINDOW_SEC)

def send_command(command_dict):
    """Sends a JSON command to CamillaDSP and returns the parsed response."""
    ws.send(json.dumps(command_dict))
    response = ws.recv()
    return json.loads(response)

def set_gain(gain_db):
    """Updates the filter parameter dynamically."""
    # CamillaDSP config value update command structure
    cmd = {
        "SetConfigValue": {
            "path": "/filters/leveliza_gain/parameters/gain",
            "value": gain_db
        }
    }
    return send_command(cmd)

# Main Loop Example
current_gain = 0.0

while True:
    try:
        # Request signal levels from CamillaDSP
        # GetSignalLevels returns a JSON structure containing playback_rms, etc.
        res = send_command({"GetSignalLevels": None})
        
        if "value" in res and "playback_rms" in res["value"]:
            rms_data = res["value"]["playback_rms"]
            
            # Extract levels for the specified channels
            k_weighted_level = rms_data[K_WEIGHTED_CHANNEL_NUMBER]
            sub_bass_level = rms_data[SUB_BASS_CHANNEL_NUMBER]

            # Check for silence or breakdown conditions
            if k_weighted_level < SILENCE_FLOOR_DB:
                print("Silence detected. Freezing gain adjustment.")
                continue  # Skip gain adjustment

            # Check for breakdown condition based on sub-bass energy
            long_bass_loudness, long_bass_loudness= sub_bass_tracker.update(sub_bass_level)



            # Update loudness tracker with K-weighted level
            short_lufs, long_lufs = lufs_tracker.update(k_weighted_level)
            
            
            # Calculate gain adjustment based on K-weighted level

    except Exception as e:
        print(f"WebSocket communication error: {e}")
        break

    time.sleep(POLL_INTERVAL_SEC)
