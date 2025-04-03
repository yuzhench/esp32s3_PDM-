import serial
import sys, select, termios, tty
import wave

# 根据实际情况修改串口名称（如 Windows: "COM3"，Linux: "/dev/ttyUSB0"）
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 921600
WAV_FILENAME = 'pcm_data.wav'

# PCM 参数
sample_rate = 16000     # 采样率
sample_width = 2        # 16位=2字节
num_channels = 1        # 单声道

# 打开串口
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print("录音线程启动")

# 设置键盘输入模式
old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())

recording = False  

# 打开 WAV 文件用于写入
wf = wave.open(WAV_FILENAME, 'wb')
wf.setnchannels(num_channels)
wf.setsampwidth(sample_width)
wf.setframerate(sample_rate)

try:
    while True:
        # 每次循环检查键盘输入，等待 0.1 秒
        dr, dw, de = select.select([sys.stdin], [], [], 0.1)
        if dr:
            key = sys.stdin.read(1)
            if key == ' ':
                recording = not recording
                if recording:
                    print("开始录音...")
                else:
                    print("结束录音，数据保存到文件：", WAV_FILENAME)
        
        if recording:
            # 读取串口数据
            data = ser.read(512)
            if data:
                wf.writeframes(data)
except KeyboardInterrupt:
    print("退出录音线程")
finally:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    ser.close()
    wf.close()
