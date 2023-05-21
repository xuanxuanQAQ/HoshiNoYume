from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.asr.v20190614 import asr_client, models
from api_key import *
import pyaudio
import webrtcvad
import io
import wave
import base64
import asyncio
import json
import openai
from io import BytesIO
import openai
import tempfile
from pydub import AudioSegment

# 录音，返回base64编码的WAV格式音频
def sound_record():
    # 设置录音参数
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    FRAME_DURATION_MS = 30
    RATE = 48000
    FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000)
    RECORD_SECONDS = 8          # 最多可录音几秒
    SILENCE_DURATION = 1      # 说完后几秒停止录音

    # 初始化pyaudio，webrtcvad
    vad = webrtcvad.Vad(3)
    audio = pyaudio.PyAudio()

    # 开启录音流
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=FRAME_SIZE)

    print("开始录音喵...")

    # 将录音记录到帧
    SILENCE_CHUNKS = int(SILENCE_DURATION * RATE / FRAME_SIZE)
    frames = []
    silence_count = 0
    first_entry = True
    filter_count = 0        # 用于滤除声音余留
    for _ in range(0, int(RATE / FRAME_SIZE * RECORD_SECONDS)):
        data = stream.read(FRAME_SIZE)
        frames.append(data)
        filter_count += 1

        if first_entry and filter_count > 11:
            if vad.is_speech(data, RATE):
                first_entry = False
        else:
            if vad.is_speech(data, RATE):
                silence_count = 0
            else:
                silence_count += 1

            if silence_count >= SILENCE_CHUNKS:
                break

    print("结束录音了捏")

    # 结束相关事件
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # 将数据帧编码为base64编码的WAV格式
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        wav_base64 = base64.b64encode(
            wav_buffer.getvalue()).decode('utf-8')

    return wav_base64

# openai whisper asr，不推荐使用，延迟太大，但是支持多语言（这个模型可进行本地部署，以后有空弄）
def whisper_asr(wav_base64):
    openai.api_key = openai_key
    audio_data_bytes = base64.b64decode(wav_base64)
    audio_data = AudioSegment.from_file(BytesIO(audio_data_bytes), format="wav")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        audio_data.export(temp_file.name, format="wav")
        transcript = openai.Audio.transcribe("whisper-1", temp_file)
    os.remove(temp_file.name)
    return transcript['text']


# 腾讯云asr,输入base64编码的wav音频，输出text，此函数需异步调用，以节约请求事件
async def tencent_asr(wav_base64):
    cred = credential.Credential(tencent_Id, tencent_key)
    # 实例化一个http选项，可选的，没有特殊需求可以跳过
    httpProfile = HttpProfile()
    httpProfile.endpoint = "asr.tencentcloudapi.com"

    # 实例化一个client选项，可选的，没有特殊需求可以跳过
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    # 实例化要请求产品的client对象,clientProfile是可选的
    client = asr_client.AsrClient(cred, "", clientProfile)
    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.SentenceRecognitionRequest()
    params = {
        "ProjectId": 0,
        "SubServiceType": 2,
        "EngSerViceType": "16k_zh",
        "SourceType": 1,
        "VoiceFormat": "wav",
        "UsrAudioKey": "0",
        "Data": wav_base64,  # 音频二进制数据
        "DataLen": len(wav_base64)  # 音频长度
    }
    req.from_json_string(json.dumps(params))
    response = await asyncio.to_thread(client.SentenceRecognition, req)

    if response.Result == "":
        print("你什么都没说~")
    else:
        print("你：" + response.Result)
    return response.Result

def listen(model:str="tencent"):
    audio_data = sound_record()
    if model == "tencent":
        user_words = asyncio.run(tencent_asr(audio_data))
        return user_words
    elif model == "whisper":
        user_words = whisper_asr(audio_data)
        return user_words
        