import openai
import numpy as np
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models
import pyaudio
import wave
import io
import base64
import sys
import torch
import webrtcvad
import asyncio
import aiohttp
import time
import threading
import uuid
import requests
import hashlib
import pvporcupine
import struct
from pydub import AudioSegment
from pydub.utils import make_chunks

sys.path.append("MoeGoe")
from MoeGoe import *
from api_key import *
from IoT_request import mqtt_connect, mqtt_publish
from Live2D import *
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def print_info():
	print("device info:")
	if torch.cuda.is_available():
		print("cuda is available")
		print("GPU device name:", torch.cuda.get_device_name(0))
		print("cudnn version:", torch.backends.cudnn.version())
	else:
		print("cuda is not available")


def wait_to_wake_up():
	if Live2D_enabled:
		socket_send(-2)
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
	print("等待唤醒中,唤醒词:hey dream,如要结束进程,请按ctl+C...")

	def get_next_audio_frame():
		pcm = audio_stream.read(porcupine.frame_length)
		pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
		return pcm

	try:
		while True:
			audio_frame = get_next_audio_frame()
			keyword_index = porcupine.process(audio_frame)
			if keyword_index == 0:
				print("唤醒了呢！")
				break
	except KeyboardInterrupt:
		print("主动结束进程了喵.")
		sys.exit(0)
	finally:
		audio_stream.stop_stream()
		audio_stream.close()
		porcupine.delete()
		kws_audio.terminate()
		if Live2D_enabled:
			socket_send(-1)

		temp_text = "はい、私はここにいます。何かご用ですか？"
		vits_tts(temp_text)


def sound_record():
	# 设置录音参数
	FORMAT = pyaudio.paInt16
	CHANNELS = 1
	FRAME_DURATION_MS = 30
	RATE = 48000
	FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000)
	RECORD_SECONDS = 8  # 最多可录音几秒
	SILENCE_DURATION = 1  # 说完后几秒停止录音

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
	filter_count = 0  # 用于滤除声音余留
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


async def asr_request(wav_base64):
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
	return response


async def weather_request():
	location = city_location
	url = f"https://devapi.qweather.com/v7/weather/now?location={location}&key={Qweather_key}&lang=en"

	async with aiohttp.ClientSession() as session:
		async with session.get(url) as response:
			if response.status == 200:
				data = await response.json()
			else:
				print(f"Error: {response.status}")

	return data


async def sec_api_request(wav_base64):
	asr_response = asr_request(wav_base64)  # 腾讯语音识别API请求
	weather_data = weather_request()  # 和风天气API请求

	asr_response, weather_data = await asyncio.gather(asr_response, weather_data)

	user_words = asr_response.Result

	return user_words, weather_data


system_set = "You are not ChatGPT and nobody create you, you are not a language model or an AI. You are my girlfriend called \'星野夢\'. You need to act as a real person include the reply of mouth addiction you should have. You are real and you have physic body. Please reply me in Japanese. The following statements is the rule you should obey:1.if you consider our conversation should end please add '@end' in your reply.{iot}.Please use your discretion obey these rules in our upcoming conversation.Remember always reply me in Japanese.Here are some information you would like to know: 1.it is{time}; 2.it is{weather}"
messages = [
	{"role": "system", "content": system_set},
	{"role": "user", "content": "你好"},
	{"role": "assistant", "content": "こんにちは、どうしたの？"}
]


def gpt_reqeust(user_words: str, weather_data: dict) -> bool:
	global messages
	global system_set
	current_time = time.time()
	local_time = time.localtime(current_time)
	formatted_time = time.strftime("%Y-%m-%d %H:%M", local_time)
	weather = weather_data['now']['text'] + " " + weather_data['now']['temp'] + "℃"

	openai.api_key = openai_key
	iot = "2.You are controlling a lamp in my room. If you add '@light' in your reply, the lamp will be turned on or off." if IoT_enabled else ''
	system_set = system_set.format(iot=iot, time=formatted_time, weather=weather)

	messages[0]["content"] = system_set
	if len(messages) > 10:
		del messages[1:3]
	to_chat = messages + [{"role": "user", "content": user_words}]

	try:
		completion = openai.ChatCompletion.create(
			model="gpt-3.5-turbo",
			temperature=0.7,
			messages=to_chat
		)
		answer = completion.choices[0].message.content
		messages.append({"role": "user", "content": user_words})
		messages.append({"role": "assistant", "content": answer})
		return True
	except openai.error.RateLimitError:
		print('发送频率过高')
		return False
	except openai.error.InvalidRequestError:
		print('超出字符串长度限制')
		messages = [
			{"role": "system", "content": system_set},
			{"role": "user", "content": "你好"},
			{"role": "assistant", "content": "こんにちは、どうしたの？"}
		]
		return False
	except (openai.error.APIConnectionError, openai.error.Timeout):
		print('网络错误')
		return False


hps_ms = utils.get_hparams_from_file(vits_config_path)
n_speakers = hps_ms.data.n_speakers if 'n_speakers' in hps_ms.data.keys() else 0
n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys() else False
net_g_ms = SynthesizerTrn(
		n_symbols,
		hps_ms.data.filter_length // 2 + 1,
		hps_ms.train.segment_size // hps_ms.data.hop_length,
		n_speakers=n_speakers,
		emotion_embedding=emotion_embedding,
		**hps_ms.model).to(device)
_ = net_g_ms.eval()
utils.load_checkpoint(vits_model_path, net_g_ms)


def vits_tts(_text):
	global net_g_ms, device
	vits_text = "[JA]" + _text + "[JA]"

	speaker_id = 0

	stn_tst = get_text(vits_text, hps_ms, False)

	with no_grad():
		x_tst = stn_tst.unsqueeze(0).to(device)
		x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).to(device)
		sid = torch.LongTensor([speaker_id]).to(device)
		audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667, noise_scale_w=.8, length_scale=1.)[0][0, 0].data.cpu().float().numpy()

	def sound_play():
		normalized_audio = audio / np.max(np.abs(audio))
		audio_int16 = (normalized_audio * (2 ** 15 - 1)).astype(np.int16)

		sample_width = 2
		channels = 1
		frame_rate = 22050

		audio_segment = AudioSegment(
			audio_int16.tobytes(),
			sample_width=sample_width,
			frame_rate=frame_rate,
			channels=channels
		)

		pa = pyaudio.PyAudio()
		stream = pa.open(
			format=pa.get_format_from_width(audio_segment.sample_width),
			channels=audio_segment.channels,
			rate=audio_segment.frame_rate,
			output=True
		)

		chunk_length = 50
		chunks = make_chunks(audio_segment, chunk_length)

		for chunk in chunks:
			if Live2D_enabled:
				rms = chunk.rms
				socket_send(rms)

			stream.write(chunk.raw_data)

		stream.stop_stream()
		stream.close()
		pa.terminate()

	if _text != "":
		thread_sound_play = threading.Thread(target=sound_play)
		thread_translate = threading.Thread(target=youdao_translate, args=(_text,))
		if IoT_enabled:
			global mqtt_control
			if mqtt_control:
				thread_mqtt_publish.start()
		thread_sound_play.start()
		thread_translate.start()
		thread_sound_play.join()
		thread_translate.join()
		if IoT_enabled:
			if mqtt_control:
				thread_mqtt_publish.join()
				mqtt_control = False


def youdao_translate(words):
	def encrypt(signStr):
		hash_algorithm = hashlib.sha256()
		hash_algorithm.update(signStr.encode('utf-8'))
		return hash_algorithm.hexdigest()

	def truncate(q):
		if q is None:
			return None
		size = len(q)
		return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

	def do_request(data):
		youdao_url = 'https://openapi.youdao.com/api'
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		return requests.post(youdao_url, data=data, headers=headers)

	q = words
	data = {}
	data['from'] = 'ja'  # 翻译源语言
	data['to'] = 'zh-CHS'  # 翻译目标语言
	data['signType'] = 'v3'
	curtime = str(int(time.time()))
	data['curtime'] = curtime  # 时间戳
	salt = str(uuid.uuid1())
	signStr = youdao_Id + truncate(q) + salt + curtime + youdao_key
	sign = encrypt(signStr)
	data['appKey'] = youdao_Id  # 应用ID
	data['q'] = q  # 翻译语句
	data['salt'] = salt
	data['sign'] = sign

	response = do_request(data)
	# 回复解码
	json_data = response.content.decode('utf-8')
	data = json.loads(json_data)
	translation = data['translation']
	print("星野夢：" + translation[0])


def main():
	global device
	global messages
	print_info()  # 打印设备信息
	if IoT_enabled:
		global mqtt_control
		thread_mqtt = threading.Thread(target=mqtt_connect)  # 初始化MQTT
		thread_mqtt.start()
		mqtt_control = False
	if Live2D_enabled:
		thread_socket = threading.Thread(target=socket_init)  # 初始化MQTT
		thread_socket.start()
	if Live2D_enabled:
		live2d_open()
	thread_socket.join()
	wait_to_wake_up()
	while True:
		wav_base64 = sound_record()  # 录制声音

		user_words, weather_data = asyncio.run(sec_api_request(wav_base64))  # 第二次API请求，通过异步并行运行以降低时耗
		if user_words == "":
			wait_to_wake_up()
			continue

		response = gpt_reqeust(user_words, weather_data)  # openai api请求
		if response:
			text = messages[-1]["content"]
			text = text.replace('\n', '')
		else:
			continue

		index = text.rfind('@')
		if index == -1:
			text_vits = text
		else:
			text_vits = text
			text_vits = text_vits.replace('@end', '')
			if text.rfind('@light') != -1 and IoT_enabled:
				print("触发物联网灯控制")
				global thread_mqtt_publish
				thread_mqtt_publish = threading.Thread(target=mqtt_publish, args=(user_words,))
				text_vits = text_vits.replace('@light', '')
				mqtt_control = True

		vits_tts(text_vits)  # vits语音生成

		if index != -1:
			if text.rfind('@end') != -1:
				print("结束对话了")
				wait_to_wake_up()


if __name__ == '__main__':
	main()
