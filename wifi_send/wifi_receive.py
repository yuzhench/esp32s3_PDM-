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
                    if len(data) >= 8:
                        # 提取前 8 个字节
                        first_8_bytes = data[:8]
                        # 用 little-endian 格式解包 4 个 16 位整数（根据具体情况选择 '<4h' 或 '>4h'）
                        pcm_samples = struct.unpack('<4h', first_8_bytes)
                        print("First 4 PCM samples:", pcm_samples)

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

if __name__ == '__main__':
    # main()
    PDM_receive()
    # record_WAV_wifi()