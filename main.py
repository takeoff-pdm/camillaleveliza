import json
import time
from websocket import create_connection

# Websocket server configuration
CAMILLADSP_ADRESS = "ws://0.0.0.0:1234"

# Channel configuration
K_WEIGHTED_CHANNEL_NUMBER = (
    0  # The channel number representing the K-weighted signal
)

# Safety boundaries & constants
MAX_BOOST_DB = 6.0  # Hard safety ceiling (positive)
MAX_CUT_DB = 24.0  # Hard safety floor (positive)
SILENCE_FLOOR_DB = -60.0  # Gate threshold for absolute silence
MAX_DECREASE_DB_PER_SEC = 1.5  # Standard pull-down speed for spikes
POLL_INTERVAL_SEC = 0.1  # Polling frequency (100ms)
EMERGENCY_THRESHOLD_DB = 4.0  # Threshold for emergency response to sudden spikes

# CamillaDSP Config Paths for Dynamic Parameters
# (These paths point to dummy filter parameters or custom gain blocks in your CamillaDSP YAML config)
PATH_TARGET_LUFS = "/filters/leveliza_target/parameters/gain"
PATH_TAU_SEC = "/filters/leveliza_tau/parameters/gain"
PATH_GAIN_OUTPUT = "/filters/leveliza_gain/parameters/gain"

# --- Leveliza State Variables ---
current_gain_db = 0.0
integrated_loudness = -14.0  # Running macro tracking anchor
last_fetched_target = -14.0
last_fetched_tau = 60.0


def send_command(command_dict):
  """Sends a JSON command to CamillaDSP and returns the parsed response."""
  ws.send(json.dumps(command_dict))
  response = ws.recv()
  return json.loads(response)


def get_config_value(path, default_value):
  """Fetches a dynamic parameter value from CamillaDSP configuration."""
  try:
    res = send_command({"GetConfigValue": path})
    if "value" in res:
      return float(res["value"])
  except Exception:
    pass
  return default_value


def set_gain(gain_db):
  """Updates the output gain parameter dynamically in CamillaDSP."""
  cmd = {"SetConfigValue": {"path": PATH_GAIN_OUTPUT, "value": gain_db}}
  return send_command(cmd)


# Establish WebSocket connection
ws = create_connection(CAMILLADSP_ADRESS)

while True:
    try:
        # 1. Fetch dynamic control values from CamillaDSP on the fly
        target_lufs = get_config_value(PATH_TARGET_LUFS, last_fetched_target)
        tau_sec = get_config_value(PATH_TAU_SEC, last_fetched_tau)
        last_fetched_target = target_lufs
        last_fetched_tau = max(
            1.0, tau_sec
        )  # Prevent division by zero or negative tau

        # Derive max increase speed dynamically based on Tau (Assertiveness)
        # Leveliza rule: ~90 seconds to recover 10dB at default slow tau (60s).
        # Scaling factor keeps recovery proportional to the chosen assertiveness speed.
        max_increase_db_per_sec = max(
            0.01, 6.6 / last_fetched_tau
        )  # Scales speed cleanly with tau

        # 2. Request signal levels from CamillaDSP
        res = send_command({"GetSignalLevels": None})

        if "value" in res and "playback_rms" in res["value"]:
            rms_data = res["value"]["playback_rms"]
            k_weighted_level = rms_data[K_WEIGHTED_CHANNEL_NUMBER]

            # 3. Silence Floor Gate: Prevent boosting noise floors
            if k_weighted_level < SILENCE_FLOOR_DB:
                print("Silence detected. Freezing gain adjustment.")
                time.sleep(POLL_INTERVAL_SEC)
                continue

            # 4. Leveliza Macro-Integration with Dynamic Tau
            # Recalculate alpha on the fly if the user changes the tau/assertiveness slider
            alpha = POLL_INTERVAL_SEC / (last_fetched_tau + POLL_INTERVAL_SEC)
            integrated_loudness = (
                1 - alpha
            ) * integrated_loudness + alpha * k_weighted_level

            # 5. Calculate Error relative to the dynamic Target LUFS
            error = target_lufs - integrated_loudness

            # 6. Asymmetrical Slew-Rate Limiting
            max_decrease_step = MAX_DECREASE_DB_PER_SEC * POLL_INTERVAL_SEC
            max_increase_step = max_increase_db_per_sec * POLL_INTERVAL_SEC

            # Emergency Response for sudden volume leaps
            instant_error = target_lufs - k_weighted_level
            if instant_error < -EMERGENCY_THRESHOLD_DB:
                effective_decrease_step = max_decrease_step * 3.0
            else:
                effective_decrease_step = max_decrease_step

            # Apply speed limits
            if error < 0:
                step = max(error, -effective_decrease_step)  # Smooth attenuation
            else:
                step = min(
                    error, max_increase_step
                )  # Glacial recovery governed by dynamic tau

            # 7. Update Gain State and Enforce Safety Boundaries
            current_gain_db += step
            current_gain_db = max(
                -MAX_CUT_DB, min(MAX_BOOST_DB, current_gain_db)
            )

            # 8. Send updated gain to CamillaDSP
            set_gain(current_gain_db)

    except Exception as e:
        print(f"WebSocket communication error: {e}")
        time.sleep(1)  # Wait a bit before retrying to avoid spamming the server

    time.sleep(POLL_INTERVAL_SEC)
