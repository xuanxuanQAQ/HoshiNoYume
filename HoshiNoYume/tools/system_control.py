import pvporcupine
import pyaudio
import struct
import torch
from api_key import *
import keyboard

# 打印设备信息
def print_device_info():
    print("device info:")
    if torch.cuda.is_available():
        print("cuda is available")
        print("GPU device name:", torch.cuda.get_device_name(0))
        print("cudnn version:", torch.backends.cudnn.version())
    else:
        print("cuda is not available")


# 进入休眠，关键词唤醒
def keyword_wake_up():
    porcupine = pvporcupine.create(
        access_key=porcupine_key,
        keyword_paths=[porcupine_model]
    )
    # 开启录音流
    kws_audio = pyaudio.PyAudio()
    audio_stream = kws_audio.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
        input_device_index=None,
    )
    print("等待唤醒中,唤醒词:hey dream...")

    def get_next_audio_frame():
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        return pcm
    try:
        while True:
            audio_frame = get_next_audio_frame()
            keyword_index = porcupine.process(audio_frame)
            if keyword_index == 0:
                print("唤醒了捏！")
                break
    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        porcupine.delete()
        kws_audio.terminate()

def press_key_wake_up():
    print("按任意键唤醒...")
    keyboard.read_event()
    print("唤醒了捏！")
