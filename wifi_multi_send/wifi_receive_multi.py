import socket
import struct

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
    HOST = ''         # 监听所有可用的网络接口
    PORT = 1234       # 监听端口（与 ESP32 端口一致）

    # 创建 TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Server listening on port {PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    # 每次最多接收 1024 字节数据
                    data = conn.recv(1024)
                    if not data:
                        print(f"Connection with {addr} closed.")
                        break

                    # 判断数据长度是否足够读取前 4 个 PCM 数据（8 字节）
                    if len(data) == 1: # this is the counter 
                        counter_index = data[0]
                       
                        print("the current received counter is: ", counter_index)

                    elif len(data) >= 8:
                        # 提取前 8 个字节
                        first_8_bytes = data[:8]
                        # 用 little-endian 格式解包 4 个 16 位整数（根据具体情况选择 '<4h' 或 '>4h'）
                        pcm_samples = struct.unpack('<4h', first_8_bytes)
                        # print("First 4 PCM samples:", pcm_samples)

                        # 将剩余数据以十六进制字符串打印出来
                        # rest_data = data[8:]
                        # print("Remaining data (hex):", rest_data.hex())
                    else:
                        print("Received data (too short):", data.hex())

                    # 可选：发送响应给客户端
                    conn.sendall(b"ACK")



def record_WAV_wifi():
    import socket
    import sys, select, termios, tty
    import wave

    # 设置监听参数
    HOST = ''          # 监听所有可用网络接口
    PORT = 1234        # 端口号（需和 ESP32 端口一致）

    # PCM 参数（根据 ESP32 端发送数据的格式设置）
    sample_rate = 16000     # 采样率
    sample_width = 2        # 16位PCM，每个样本2字节
    num_channels = 1        # 单声道
    WAV_FILENAME = 'wifi_pcm_data.wav'

    # 创建 TCP 服务器并监听连接
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # 设置键盘输入模式（适用于 Unix/Linux）
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    recording = False  # 录音状态开关

    # 打开 WAV 文件用于写入（整个过程中始终打开，根据录音状态判断是否写入数据）
    wf = wave.open(WAV_FILENAME, 'wb')
    wf.setnchannels(num_channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)

    print("按空格键开始/停止录音，Ctrl+C退出。")

    try:
        while True:
            # 同时监听键盘输入和网络数据，等待0.1秒
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)
            
            # 检查是否有键盘输入
            if sys.stdin in ready_to_read:
                key = sys.stdin.read(1)
                if key == ' ':
                    recording = not recording
                    if recording:
                        print("开始录音...")
                    else:
                        print("结束录音，数据保存到文件：", WAV_FILENAME)
            
            # 检查是否有网络数据到达
            if conn in ready_to_read:
                data = conn.recv(512)
                if not data:
                    print("客户端断开连接")
                    break
                # 如果处于录音状态，将数据写入 WAV 文件
                if recording:
                    wf.writeframes(data)
    except KeyboardInterrupt:
        print("退出录音程序")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf.close()


def recv_all(conn, length):
    """
    确保从连接中接收指定长度的数据，否则返回 None。
    """
    data = b""
    while len(data) < length:
        more = conn.recv(length - len(data))
        if not more:
            return None
        data += more
    return data


def bag_513():
    HOST = ""   # 监听所有网络接口
    PORT = 1234 # 与 ESP32 端口保持一致

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on port {PORT}...")

    while True:
        conn, addr = server_socket.accept()
        print("Connected by", addr)
        with conn:
            while True:
                # 先接收包头：2字节，表示后续数据包的长度（网络字节序）
                header = recv_all(conn, 2)
                if header is None:
                    print("连接关闭或读取包头失败")
                    break
                # 使用 '!H' 格式解包（无符号短整型，网络字节序）
                packet_length, = struct.unpack("!H", header)
                
                # 根据包头中的长度接收完整数据包
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("连接关闭或读取数据包失败")
                    break
                
                # 假设协议定义数据包长度固定为513字节：
                # 前512字节为音频数据，最后1字节为计数器
                if packet_length != 513:
                    print("收到异常长度的数据包：", packet_length)
                else:
                    audio_data = packet[:-1]  # 前512字节：音频数据
                    counter = packet[-1]      # 最后1字节：计数器
                    print("收到音频数据长度：", len(audio_data), "计数器：", counter)
                    
                    # 此处可以进一步处理 audio_data（例如保存到文件等）
        print("客户端断开连接")

    server_socket.close()

import sys, select, termios, tty, struct, wave

def record_WAV_wifi_513():
    HOST = ''          # 监听所有网络接口
    PORT = 1234        # 端口号（需与ESP32端一致）

    # PCM参数（根据ESP32发送的数据格式设置）
    sample_rate = 16000     # 采样率
    sample_width = 2        # 16位PCM，每个样本2字节
    num_channels = 1        # 单声道
    WAV_FILENAME = 'wifi_pcm_data.wav'

    # 创建TCP服务器并监听连接
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # 设置键盘输入模式（适用于Unix/Linux）
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    recording = False  # 录音状态开关

    # 打开WAV文件用于写入
    wf = wave.open(WAV_FILENAME, 'wb')
    wf.setnchannels(num_channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)

    print("按空格键开始/停止录音，Ctrl+C退出。")

    last_counter = None
    try:
        while True:
            # 同时监听键盘输入和网络数据，等待0.1秒
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)

            # 检查是否有键盘输入
            if sys.stdin in ready_to_read:
                key = sys.stdin.read(1)
                if key == ' ':
                    recording = not recording
                    if recording:
                        print("开始录音...")
                    else:
                        print("结束录音，数据保存到文件：", WAV_FILENAME)

            # 检查网络数据
            if conn in ready_to_read:
                # 先接收包头：2字节，表示后续数据包的总长度（网络字节序）
                header = recv_all(conn, 2)
                if header is None:
                    print("连接关闭或读取包头失败")
                    break
                # 使用 '!H' 格式解包（无符号短整型，网络字节序）
                packet_length, = struct.unpack("!H", header)
                
                # 根据包头中的长度接收完整数据包
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("连接关闭或读取数据包失败")
                    break
                
                # 协议定义：数据包长度固定为513字节
                # 前512字节为音频数据，最后1字节为计数器
                if packet_length != 513:
                    print("收到异常长度的数据包：", packet_length)
                else:
                    audio_data = packet[:-1]  # 前512字节：音频数据
                    counter = packet[-1]      # 最后1字节：计数器
                    if recording:
                        print("收到音频数据长度：", len(audio_data), "计数器：", counter)
                        if last_counter != None and counter - last_counter != 1 and counter != 0:
                            print("warning!!! we lost one package")
                        last_counter = counter 
                    
                    # 如果处于录音状态，则将音频数据写入WAV文件
                    if recording:
                        wf.writeframes(audio_data)
    except KeyboardInterrupt:
        print("退出录音程序")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf.close()

    #checking the counter: 



def record_WAV_wifi_1025():
    HOST = ''          # 监听所有网络接口
    PORT = 1234        # 端口号（需与ESP32端一致）

    # ========== WAV文件参数设置 ==========
    sample_rate = 16000      # 采样率
    sample_width = 2         # 每个样本2字节(16位)
    num_channels = 1         # 这里将左右声道分到两个单声道文件
    left_wav_filename = 'wifi_pcm_data_channle1.wav'
    right_wav_filename = 'wifi_pcm_data_channle2.wav'

    # ========== 创建TCP服务器，监听连接 ==========
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Server listening on port {PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # ========== 设置非阻塞读取键盘输入（适用于Unix/Linux） ==========
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    recording = False  # 录音状态开关

    # ========== 创建两个WAV文件，分别存左/右声道（单声道） ==========
    wf_left = wave.open(left_wav_filename, 'wb')
    wf_left.setnchannels(num_channels)   # 单声道
    wf_left.setsampwidth(sample_width)   # 16位PCM
    wf_left.setframerate(sample_rate)    # 16k采样率

    wf_right = wave.open(right_wav_filename, 'wb')
    wf_right.setnchannels(num_channels)  # 单声道
    wf_right.setsampwidth(sample_width)  # 16位PCM
    wf_right.setframerate(sample_rate)   # 16k采样率

    print("按空格键开始/停止录音，Ctrl+C退出。")

    last_counter = None
    try:
        while True:
            # 同时监听键盘输入和网络数据，等待0.1秒
            ready_to_read, _, _ = select.select([sys.stdin, conn], [], [], 0.1)

            # ========== 检查键盘输入，用空格切换录音状态 ==========
            if sys.stdin in ready_to_read:
                key = sys.stdin.read(1)
                if key == ' ':
                    recording = not recording
                    if recording:
                        print("开始录音...")
                    else:
                        print("结束录音，数据保存到文件：", left_wav_filename, right_wav_filename)

            # ========== 检查网络数据 ==========
            if conn in ready_to_read:
                # 1) 先接收包头2字节，表示后续数据包总长度（网络字节序）
                header = recv_all(conn, 2)
                if header is None:
                    print("连接关闭或读取包头失败")
                    break
                packet_length, = struct.unpack("!H", header)

                # 2) 接收该长度的完整数据包
                packet = recv_all(conn, packet_length)
                if packet is None:
                    print("连接关闭或读取数据包失败")
                    break

                # === 根据ESP32的发送协议： 1025字节 = 1024字节音频 + 1字节计数器 ===
                if packet_length != 1025:
                    print("收到异常长度的数据包：", packet_length)
                    # 可以根据需求选择 continue 或 break
                    continue
                else:
                    # 拆分出音频数据(前1024字节)和计数器(最后1字节)
                    audio_data = packet[:-1]  # 1024 字节音频
                    counter = packet[-1]      # 计数器

                    # 如果正在录音，则打印包信息
                    if recording:
                        print("收到音频数据长度：", len(audio_data), "计数器：", counter)
                        if last_counter is not None and counter - last_counter != 1 and counter != 0:
                            print("warning!!! we lost one package")
                        last_counter = counter

                    # ========== 拆分左右声道 ==========
                    # 此时 audio_data 每4个字节包含 (左声道16bit + 右声道16bit)
                    # left_samples  就取  [0:2, 4:6, 8:10, ...]
                    # right_samples 就取  [2:4, 6:8, 10:12, ...]
                    left_samples = b"".join(
                        [audio_data[i:i+2] for i in range(0, len(audio_data), 4)]
                    )
                    right_samples = b"".join(
                        [audio_data[i+2:i+4] for i in range(0, len(audio_data), 4)]
                    )

                    # ========== 如果处于录音状态，则分别写入左右声道文件 ==========
                    if recording:
                        wf_left.writeframes(left_samples)
                        wf_right.writeframes(right_samples)

    except KeyboardInterrupt:
        print("退出录音程序")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        conn.close()
        server_socket.close()
        wf_left.close()
        wf_right.close()

if __name__ == '__main__':
    # main()
    # PDM_receive()
    # record_WAV_wifi()
    # bag_513()
    # record_WAV_wifi_513()
    record_WAV_wifi_1025()