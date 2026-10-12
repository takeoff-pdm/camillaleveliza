from collections import deque
import math

class LoudnessTracker:
    def __init__(self, poll_interval_sec, short_window_sec, long_window_sec):
        # Calculate maximum length (number of samples) for each deque
        self.short_maxlen = int(short_window_sec / poll_interval_sec)
        self.long_maxlen = int(long_window_sec / poll_interval_sec)
        
        # Initialize FIFO deques for linear power values
        self.short_window = deque(maxlen=self.short_maxlen)
        self.long_window = deque(maxlen=self.long_maxlen)

    def update(self, db_value):
        """
        Takes raw dBFS from CamillaDSP, converts to linear power, 
        pushes to FIFO buffers, and returns rolling averages in dB.
        """
        # Handle floor silence to avoid math domain errors (-inf)
        if db_value <= -96.0:
            linear_power = 0.0
        else:
            # Step 1: Convert dB to linear power (RMS squared equivalent)
            linear_power = 10.0 ** (db_value / 10.0)

        # Step 2: Push into both FIFO queues
        self.short_window.append(linear_power)
        self.long_window.append(linear_power)

        # Step 3: Compute rolling averages (mean of linear power -> convert back to dB)
        short_db = self._power_to_db(sum(self.short_window) / len(self.short_window))
        long_db = self._power_to_db(sum(self.long_window) / len(self.long_window))

        return short_db, long_db

    def _power_to_db(self, power):
        if power <= 0.0:
            return -96.0
        return 10.0 * math.log10(power)
