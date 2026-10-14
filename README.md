# camillaleveliza
A hardware-inspired, RC Audio Leveliza-style automated loudness leveler built in Python for real-time electronic music and live DSP environments via CamillaDSP WebSockets.

Unlike standard compressors that pump and distort on heavy sub-bass breakdowns, this script mimics analog electronic physics to maintain rock-solid perceived loudness across varying track arrangements without altering transient punch.

# Key Features
Analog RC-Circuit Emulation: Uses a dynamic exponential moving average (tau) to track long-term macro loudness, preventing 32-bar breakdowns and quiet intros from triggering unwanted volume boosts.

Asymmetrical Slew Limiting: Provides instant, transparent attenuation for sudden DJ fader jumps or aggressive peaks, paired with a glacial recovery rate (~90 seconds for a full 10 dB) to ensure zero audible pumping.

Live Dynamic Control: Communicates directly with CamillaDSP via WebSockets to fetch and update Target LUFS and Tau (Assertiveness) parameters on the fly, allowing for tactile MIDI or GUI control during live sets.

Silence Gate: Automatically freezes gain adjustments during absolute silence or noise floors to prevent background noise swelling.
