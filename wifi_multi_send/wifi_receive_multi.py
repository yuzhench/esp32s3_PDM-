import socket
import struct
import sys, select, termios, tty, wave
import numpy as np
import threading
from queue import Queue
import whisper
from datetime import datetime, timedelta
from time import sleep
from sys import platform
import torch
import os
import threading 

def main():
    HOST = ''         # Listen on all available network interfaces
    PORT = 1234       # Port to listen on (must match the ESP32 configuration)

    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the socket to the host and port
        s.bind((HOST, PORT))
        # Listen for incoming connections (allowing 1 connection in the backlog)
        s.listen(1)
        print(f"Server listening on port {PORT}...")

        while True:
            # Wait for a connection
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    # Receive data from the client (max 1024 bytes)
                    data = conn.recv(1024)
                    if not data:
                        print(f"Connection with {addr} closed.")
                        break
                    # Decode and print the received data
                    print("Received:", data.decode())
                    # Optionally, send a response back to the client (e.g., "ACK")
                    conn.sendall(b"ACK")

def PDM_receive():
    HOST = ''         # Listen on all available network interfaces
    PORT = 1234       # Listening port (must match the ESP32 configuration)

    # Create TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Server listening on port {PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    # Receive up to 1024 bytes of data each time
                    data = conn.recv(1024)
                    if not data:
                        print(f"Connection with {addr} closed.")
                        break

                    # Check if data length is enough to read the first 4 PCM data (8 bytes)
                    if len(data) == 1:  # this is the counter
                        counter_index = data[0]
                        print("The current received counter is:", counter_index)

                    elif len(data) >= 8:
                        # Extract the first 8 bytes
                        first_8_bytes = data[:8]
                        # Unpack 4 x 16-bit integers using little-endian format ('<4h' or '>4h')
                        pcm_samples = struct.unpack('<4h', first_8_bytes)
                        # print("First 4 PCM samples:", pcm_samples)

                        # Print the remaining data in hex string format
                        # rest_data = data[8:]
                        # print("Remaining data (hex):", rest_data.hex())
                    else:
                        print("Received data (too short):", data.hex())

                    # Optional: send a response back to the client
                    conn.sendall(b"ACK")

def record_WAV_wifi():
    import socket
    import sys, select, termios, tty
    import wave

    # Set listening parameters
    HOST = ''          # Listen on all available network interfaces
    PORT = 1234        # Port (must match ESP32 side)

    # PCM parameters (based on the ESP32 data format)
    sample_rate = 16000     # Sampling rate
    sample_width = 2        # 16-bit PCM, 2 bytes per sample
    num_channels = 1        # Mono
    WAV_FILENAME = 'wifi_pcm_data.wav'

    # Create TCP server and listen for connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # Set the keyboard input mode (for Unix/Linux)
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    recording = False  # Recording state switch

    # Open the WAV file for writing (opened throughout, only write if recording)
    wf = wave.open(WAV_FILENAME, 'wb')
    wf.setnchannels(num_channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)

    print("Press space to start/stop recording, Ctrl+C to exit.")

    try:
        while True:
            # Simultaneously monitor keyboard input and network data, wait 0.1s
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)
            
            # Check if there is keyboard input
            if sys.stdin in ready_to_read:
                key = sys.stdin.read(1)
                if key == ' ':
                    recording = not recording
                    if recording:
                        print("Start recording...")
                    else:
                        print("Stop recording, data saved to file:", WAV_FILENAME)
            
            # Check if there is network data
            if conn in ready_to_read:
                data = conn.recv(512)
                if not data:
                    print("Client disconnected")
                    break
                # If in recording state, write data to WAV file
                if recording:
                    wf.writeframes(data)
    except KeyboardInterrupt:
        print("Exiting the recording program")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf.close()

def recv_all(conn, length):
    """
    Ensure the specified length of data is received from the connection, or return None if not possible.
    """
    data = b""
    while len(data) < length:
        more = conn.recv(length - len(data))
        if not more:
            return None
        data += more
    return data

def bag_513():
    HOST = ""   # Listen on all network interfaces
    PORT = 1234 # Must match the ESP32 port

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on port {PORT}...")

    while True:
        conn, addr = server_socket.accept()
        print("Connected by", addr)
        with conn:
            while True:
                # First receive the header: 2 bytes, indicating the length of the subsequent data packet (network byte order)
                header = recv_all(conn, 2)
                if header is None:
                    print("Connection closed or failed to read header")
                    break
                # Use '!H' format to unpack (unsigned short, network byte order)
                packet_length, = struct.unpack("!H", header)
                
                # Receive the complete data packet according to the length in the header
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("Connection closed or failed to read data packet")
                    break
                
                # Assume protocol defines a fixed data packet length of 513 bytes:
                # The first 512 bytes are audio data, the last 1 byte is a counter
                if packet_length != 513:
                    print("Received abnormal-length data packet:", packet_length)
                else:
                    audio_data = packet[:-1]  # The first 512 bytes: audio data
                    counter = packet[-1]      # The last byte: counter
                    print("Received audio data length:", len(audio_data), "Counter:", counter)
                    
                    # Further process audio_data here (e.g., save to file)
        print("Client disconnected")

    server_socket.close()

def record_WAV_wifi_513():
    HOST = ''          # Listen on all network interfaces
    PORT = 1234        # Port number (must match the ESP32 side)

    # PCM parameters (according to the data format sent by the ESP32)
    sample_rate = 16000     # Sampling rate
    sample_width = 2        # 16-bit PCM, 2 bytes per sample
    num_channels = 1        # Mono
    WAV_FILENAME = 'wifi_pcm_data.wav'

    # Create a TCP server and listen for connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # Set up keyboard input mode (for Unix/Linux)
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    recording = False  # Recording state switch

    # Open the WAV file for writing
    wf = wave.open(WAV_FILENAME, 'wb')
    wf.setnchannels(num_channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)

    print("Press space to start/stop recording, Ctrl+C to exit.")

    last_counter = None
    try:
        while True:
            # Simultaneously listen for keyboard input and network data for 0.1 seconds
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)

            # Check for keyboard input
            if sys.stdin in ready_to_read:
                key = sys.stdin.read(1)
                if key == ' ':
                    recording = not recording
                    if recording:
                        print("Start recording...")
                    else:
                        print("Stop recording, data saved to file:", WAV_FILENAME)

            # Check network data
            if conn in ready_to_read:
                # First receive the 2-byte header (total length of the subsequent data packet, network byte order)
                header = recv_all(conn, 2)
                if header is None:
                    print("Connection closed or failed to read the header")
                    break
                packet_length, = struct.unpack("!H", header)
                
                # Receive the complete data packet according to the length in the header
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("Connection closed or failed to read the data packet")
                    break
                
                # Protocol definition: data packet length is fixed at 513 bytes
                # The first 512 bytes are audio data, the last 1 byte is the counter
                if packet_length != 513:
                    print("Received abnormal-length data packet:", packet_length)
                else:
                    audio_data = packet[:-1]
                    counter = packet[-1]
                    if recording:
                        print("Received audio data length:", len(audio_data), "Counter:", counter)
                        if last_counter is not None and counter - last_counter != 1 and counter != 0:
                            print("Warning!!! We lost one package")
                        last_counter = counter

                    # If recording, write the audio data to the WAV file
                    if recording:
                        wf.writeframes(audio_data)
    except KeyboardInterrupt:
        print("Exiting the recording program")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf.close()

def record_WAV_wifi_1025():
    HOST = ''          # Listen on all network interfaces
    PORT = 1234        # Port number (must match the ESP32 side)

    # ========== WAV file parameter settings ==========
    sample_rate = 16000      # Sampling rate
    sample_width = 2         # 16-bit per sample (2 bytes)
    num_channels = 1         # We'll split left/right into two mono files
    left_wav_filename = 'wifi_pcm_data_channle1.wav'
    right_wav_filename = 'wifi_pcm_data_channle2.wav'

    # ========== Create a TCP server and listen for connections ==========
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # ========== Set non-blocking keyboard input reading (for Unix/Linux) ==========
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    # recording = False  # Recording state switch

    # ========== Create two WAV files for left/right channels (mono) ==========
    wf_left = wave.open(left_wav_filename, 'wb')
    wf_left.setnchannels(num_channels)
    wf_left.setsampwidth(sample_width)
    wf_left.setframerate(sample_rate)

    wf_right = wave.open(right_wav_filename, 'wb')
    wf_right.setnchannels(num_channels)
    wf_right.setsampwidth(sample_width)
    wf_right.setframerate(sample_rate)

    print("Press space to start/stop recording, Ctrl+C to exit.")

    last_counter = None

    left_buffer = b''
    right_buffer = b''


    try:
        while True:
            # Listen for keyboard input and network data for 0.1 seconds
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)

            # ========== Check keyboard input, use space to toggle recording state ==========
            # if sys.stdin in ready_to_read:
            #     key = sys.stdin.read(1)
            #     if key == ' ':
            #         recording = not recording
            #         if recording:
            #             print("Start recording...")
            #         else:
            #             print("Stop recording, data saved to files:", left_wav_filename, right_wav_filename)

            # ========== Check network data ==========
            if conn in ready_to_read:
                # 1) First receive 2-byte header, indicating total length of subsequent data packet (network byte order)
                header = recv_all(conn, 2)
                if header is None:
                    print("Connection closed or failed to read header")
                    break
                packet_length, = struct.unpack("!H", header)

                # 2) Receive the complete data packet of that length
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("Connection closed or failed to read data packet")
                    break

                # === According to the ESP32 sending protocol: 1025 bytes = 1024 bytes of audio + 1 byte counter ===
                if packet_length != 1025:
                    print("Received abnormal-length data packet:", packet_length)
                    continue
                else:
                    # Separate the audio data (first 1024 bytes) and the counter (last 1 byte)
                    audio_data = packet[:-1]
                    counter = packet[-1]

                    # If recording, print package information
                    if running_event.is_set():
                        # print("Received audio data length:", len(audio_data), "Counter:", counter)
                        if last_counter is not None and counter - last_counter != 1 and counter != 0:
                            print("Warning!!! we lost one package")
                        last_counter = counter

                    # ========== Separate left and right channels ==========
                    # Each 4 bytes in audio_data contain (left channel 16-bit + right channel 16-bit)
                    left_samples = b"".join(
                        [audio_data[i:i+2] for i in range(0, len(audio_data), 4)]
                    )
                    right_samples = b"".join(
                        [audio_data[i+2:i+4] for i in range(0, len(audio_data), 4)]
                    )

                    # ========== If recording, write to left and right channel files ==========
                    if running_event.is_set():
                        wf_left.writeframes(left_samples)
                        wf_right.writeframes(right_samples)

                       

                    if running_event.is_set():
                        left_buffer += left_samples #prepare for the whisper model
                        right_buffer += right_samples

                        # if len(left_buffer) >= 64000:
                           
                        #     chunk_left = left_buffer 
                        #     chunk_right = right_buffer


                        #     #transfer to numpy 
                        #     chunk_left_narray = np.frombuffer(chunk_left, dtype=np.int16)

                        #     data_queue.put(left_buffer)

                            

                        #     left_buffer = b''
                        #     right_buffer = b''
                        #     # print("clean the buffer")


                        #classical microphone 
                        if len(right_buffer) >= 64000:
                           
                           
                            chunk_right = right_buffer


                            #transfer to numpy 
                            chunk_left_narray = np.frombuffer(chunk_right, dtype=np.int16)

                            data_queue.put(right_buffer)

                            

                            right_buffer = b''
                            # print("clean the buffer")
    except KeyboardInterrupt:
        print("Exiting the recording program")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf_left.close()
        wf_right.close()



def whisper_real_time():
    phrase_time = None
    while True:
        try:
            now = datetime.utcnow()
            # If the queue is not empty, grab the data from the queue
            if not data_queue.empty():

                phrase_complete = False
                # Check if the waiting time is long enough for a new sentence 
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_complete = True
                
                # Update the time for when the most recent data is received
                phrase_time = now
                
                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()
                
                # Convert in-ram buffer to something the model can use
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Read the transcription.
                result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system('cls' if os.name=='nt' else 'clear') 
                for line in transcription:
                    print(line)
                # Flush stdout.
                print('', end='', flush=True)
            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            print("\n\nTranscription:")
            for line in transcription:
                print(line)
            np.savetxt('strings.txt', transcription, fmt='%s')
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)


def keyboard_listener():
 
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    print("")
    try:
        while not exit_event.is_set():
            c = sys.stdin.read(1)
            if c == ' ':
                # 切换 running_event 的状态
                if running_event.is_set():
                    running_event.clear()
                    print("[keyboard_listener] >>> stopped")
                else:
                    running_event.set()
                    print("[keyboard_listener] >>> started")

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("[keyboard_listener] quite")

        # 如果想在按 Ctrl+C 时让整个程序都退出，可以 set exit_event
        exit_event.set()


if __name__ == '__main__':
    # # main()
    # # PDM_receive()
    # # record_WAV_wifi()
    # # bag_513()
    # # record_WAV_wifi_513()


    """multi threading"""


    #parameter setting 

    running_event = threading.Event()  
    exit_event = threading.Event()

    audio_model = whisper.load_model("medium", download_root="/home/yuzhen/esp/PDM_microphone/wifi_multi_send")
    phrase_timeout = 0
    phrase_time = None
    transcription = ['']
    data_queue = Queue()

    # # Cue the user that we're ready to go.
    # print("Listening for WiFi audio and starting transcription...")
    # thread = threading.Thread(target=record_WAV_wifi_1025)
    # thread.start()

    # whisper_real_time()


    # record_WAV_wifi_1025()


    whisper_thread = threading.Thread(target=whisper_real_time, daemon=True)
    record_thread = threading.Thread(target=record_WAV_wifi_1025, daemon=True)
    t_key     = threading.Thread(target=keyboard_listener, daemon=True)

    whisper_thread.start()
    record_thread.start()
    t_key.start()

    try:
        whisper_thread.join()
        record_thread.join()
    except KeyboardInterrupt:
        print("main thread capture key point interruption")



    

    
