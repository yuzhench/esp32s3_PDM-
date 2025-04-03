import wave

RAW_FILENAME = 'pcm_data.raw'
WAV_FILENAME = 'pcm_data.wav'

# PCM 参数
sample_rate = 16000     # 采样率
sample_width = 2        # 16位=2字节
num_channels = 1        # 单声道

# 读取 raw 数据
with open(RAW_FILENAME, 'rb') as rf:
    raw_data = rf.read()

# 创建 WAV 文件并写入数据
with wave.open(WAV_FILENAME, 'wb') as wf:
    wf.setnchannels(num_channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)
    wf.writeframes(raw_data)

print("转换完成，生成文件：", WAV_FILENAME)
