# import serial
# import sys, select, termios, tty

# # 根据实际情况修改串口名称（如 Windows: "COM3"，Linux: "/dev/ttyUSB0"）
# SERIAL_PORT = '/dev/ttyUSB0'
# BAUD_RATE = 921600
# RAW_FILENAME = 'pcm_data'

# counter = 0
# # 打开串口
# ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
# print("recording thread start")

# # button checking
# old_settings = termios.tcgetattr(sys.stdin)
# tty.setcbreak(sys.stdin.fileno())

# recording = False  

# try:
#     while True:
#         with open(f"{RAW_FILENAME}{counter}.raw", 'wb') as f:
#             #wait for keyboad input for 0.1 second
#             dr, dw, de = select.select([sys.stdin], [], [], 0.1)
#             if dr:
#                 key = sys.stdin.read(1)
#                 if key == ' ':
#                     recording = not recording
#                     if recording:
#                         print("start recording...")
#                     else:
#                         print("end recording...")
#                         print(f"recorded the raw PCM signal to the", f"{RAW_FILENAME}{counter}.raw" , "file")
#                         counter+=1
            
#             #start to read in data
#             if recording:
#                 data = ser.read(512)
#                 if data:
#                     f.write(data)
# except KeyboardInterrupt:
#     print("quite the recording thread")
# finally:
#     termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
#     ser.close()









import serial
import time
import wave
import os
 

 
 
def main():
    """parameter definition"""
    FILENAME = 'wave2000Hz'
    recording = True

    # 修改下面的串口号为你的 ESP32 所连接的串口
    serial_port = '/dev/ttyUSB0'  # Windows 示例；Linux 下可能为 "/dev/ttyUSB0"
    baud_rate = 921600
    timeout = 1  # 超时设置，单位秒

    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=timeout)
        print(f"打开串口 {serial_port} 成功，开始接收数据...")
    except serial.SerialException as e:
        print(f"无法打开串口: {e}")
        return
    
     

    # 打开文件以二进制写模式保存 raw 数据
 
      
             
    RAW_FILENAME = f"{FILENAME}.raw"
    WAV_FILENAME = f"{FILENAME}.wav"
    with open(RAW_FILENAME, "wb") as raw_file:
        try:
            while True:
                # 每次读取 1024 字节（可根据需求调整）
                data = ser.read(512)
                if data:
                    raw_file.write(data)
                    raw_file.flush()  # 实时写入文件
                else:
                    # 如果没有数据，可以短暂休眠后继续读取
                    time.sleep(0.01)
        except KeyboardInterrupt:
            print("接收数据被中断，正在退出...")
        finally:
            ser.close()
            print("串口已关闭，数据保存在 pcm_data.raw 中。")

        
            """start to translate to WAV file"""
            

            # PCM 参数
            sample_rate = 16000     # 采样率
            sample_width = 2        # 16位=2字节
            num_channels = 1        # 单声道

            # 读取 raw 数据
            with open(RAW_FILENAME, 'rb') as rf:
                raw_data = rf.read()

            os.remove(RAW_FILENAME)

            # 创建 WAV 文件并写入数据
            with wave.open(WAV_FILENAME, 'wb') as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(sample_rate)
                wf.writeframes(raw_data)

            print("转换完成，生成文件：", WAV_FILENAME)
          
 


if __name__ == "__main__":
    main()
