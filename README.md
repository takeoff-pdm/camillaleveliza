# camillaleveliza
Leveliza algorithm build for CamillaDSP by HEEnquist build with pycamilladsp

# What does it do
The goal is to help levelize the average perceived loudness. This might be useful with live concerts, DJs and other audio content that might drift in perceived loudness over time without intent. It should not compress or even limit the dynamic range of the audio content, but is intended to smooth fluctuations out.

E.g. a DJ mixes the next track in which is 3db louder than the track before or the FOH Mix Engineer does not notice that the average loudness rose or fell by a certain amount.

In other words, it is designed to reduce the amount of loudness correction a sound device operator might encounter and simulate the same behavior of one. It is specifically designed for PA situations with focus on EDM and was tested in those. The calibration for other types of setups might need adjustment.

# How does it (try to) accomplish this
1. Perceived Loudness Engine
Reads the RMS Loudness of a K-Weighted Filter of the input channel and adjust it accordingly in two different modes
2. Smart Attack & Release
When suddenly the loudness cranks up the system has a faster emergency reduction build in. With slower increases or decreases, slow loudness adjustments are taken.
3. Contextual Adjustments
As it is build for musical content, especially for EDM, it detects breakdowns, drops and silence to not confuse those with sudden loudness reductions or increases. This is achieved by having a loudness increase limit and detecting bass energy and freezing the loudness increase algorithm for the time being.
4. Multichannel Linkage
For all channels that play different tracks of the same audio content (e.g. L and R for Stereo) the reduction and increase have the same value (they are linked).
5. Adjustment boundaries
Attenuation and Boost have maximum values that can be adjusted
