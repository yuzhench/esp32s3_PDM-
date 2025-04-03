import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile

# Specify the path to your WAV file
wav_file = 'wave2000Hz.wav'  # Replace with your WAV file path

# Read the WAV file
sample_rate, data = wavfile.read(wav_file)
print(f"Sample rate: {sample_rate} Hz")
print(f"Number of samples: {len(data)}")

# If the audio data has multiple channels (e.g., stereo), select the first channel
if data.ndim > 1:
    data = data[:, 0]

# Generate a time axis based on the sample rate and number of samples
duration = len(data) / sample_rate
time = np.linspace(0, duration, num=len(data))

# Plot the waveform
plt.figure(figsize=(12, 4))
plt.plot(time, data, color='blue')
plt.title('Waveform of the WAV File')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude')
plt.grid(True)
plt.tight_layout()
plt.show()



# ----- New Functionality: Calculate and Plot Frequency Spectrum -----


# Compute the Fast Fourier Transform (FFT) of the audio signal
fft_data = np.fft.fft(data)
# Calculate the magnitude spectrum
fft_magnitude = np.abs(fft_data)
# Generate frequency bins corresponding to FFT data
frequencies = np.fft.fftfreq(len(data), d=1/sample_rate)

# Since the FFT output is symmetric, take only the positive half of the frequencies
half_length = len(frequencies) // 2
frequencies = frequencies[:half_length]
fft_magnitude = fft_magnitude[:half_length]

# Find the dominant frequency (frequency with maximum magnitude)
dominant_frequency = frequencies[np.argmax(fft_magnitude)]
print(f"Dominant frequency: {dominant_frequency} Hz")

# Plot the frequency spectrum
plt.figure(figsize=(12, 4))
plt.plot(frequencies, fft_magnitude, color='red', label='Frequency Spectrum')
# Add a vertical line and annotation for the dominant frequency
plt.axvline(x=dominant_frequency, color='green', linestyle='--', 
            label=f'Dominant Frequency: {dominant_frequency:.2f} Hz')
plt.title('Frequency Spectrum of the WAV File')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()



import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks

# ---------------------------
# 4. Zoom In Based on the Dominant Frequency Period Using Peak Detection
# ---------------------------
# Calculate the period corresponding to the dominant frequency (in seconds)
if dominant_frequency <= 0:
    print("Unable to zoom in based on the dominant frequency because it is 0 or negative.")
else:
    period = 1.0 / dominant_frequency
    print(f"One period of dominant frequency: {period} seconds")

    # Assume we want to view 3 cycles; calculate the duration needed
    num_cycles = 3
    zoom_duration = period * num_cycles  # duration for 3 cycles

    # Convert zoom_duration into number of samples (rounded)
    zoom_samples = int(zoom_duration * sample_rate)

    # For simplicity, extract the first 3 cycles from the beginning of the audio
    start_index = 0
    end_index = min(len(data), zoom_samples)

    # Extract the time-domain data for the zoomed portion
    zoomed_data = data[start_index:end_index]
    zoomed_time = np.linspace(0, zoom_duration, num=len(zoomed_data))

    plt.figure(figsize=(12, 4))
    plt.plot(zoomed_time, zoomed_data, label="Zoomed Waveform")

    # Use peak detection to find peaks in the zoomed waveform.
    # Adjust the 'height' threshold as necessary; here we use 50% of the maximum amplitude.
    peaks, properties = find_peaks(zoomed_data, height=0.5 * np.max(zoomed_data))
    peak_times = zoomed_time[peaks]

    # Mark the detected peaks with red circles.
    plt.plot(peak_times, zoomed_data[peaks], "ro", label="Detected Peaks")

    # Draw vertical dashed lines at each detected peak.
    for i, t in enumerate(peak_times):
        plt.axvline(x=t, color='green', linestyle='--', label="Peak" if i == 0 else None)

    # If at least two peaks are detected, estimate the period from the differences.
    if len(peak_times) > 1:
        periods = np.diff(peak_times)
        avg_period = np.mean(periods)
        estimated_frequency = 1.0 / avg_period
        annotation_text = (f"Estimated Period: {avg_period:.4f} s\n"
                           f"Estimated Frequency: {estimated_frequency:.2f} Hz")
    else:
        annotation_text = "Not enough peaks detected to estimate period"

    # Annotate the plot with the estimated period and frequency.
    plt.text(0.05 * zoom_duration, 0.9 * np.max(zoomed_data),
             annotation_text, fontsize=12, color='purple')

    plt.title(f'Zoomed Waveform with Detected Peaks (First {num_cycles} Cycles)')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()