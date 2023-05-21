from api_key import *
import torch
import pyaudio
from pydub import AudioSegment
from pydub.utils import make_chunks
from actions.Live2D import socket_send
from tools.translate import text2text_translate
import sys
import numpy as np
import azure.cognitiveservices.speech as speechsdk

sys.path.append("HoshiNoYume\\actions\\MoeGoe")
from MoeGoe import *
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def vits_tts(text):
    if ai_language == "Chinese":
        vits_text = "[CH]" + text + "[CH]"
    else:
        vits_text = "[JA]" + text + "[JA]"
    model = vits_model_path
    config = vits_config_path

    hps_ms = utils.get_hparams_from_file(config)
    n_speakers = hps_ms.data.n_speakers if 'n_speakers' in hps_ms.data.keys() else 0
    n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
    emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys() else False

    net_g_ms = SynthesizerTrn(
        n_symbols,
        hps_ms.data.filter_length // 2 + 1,
        hps_ms.train.segment_size // hps_ms.data.hop_length,
        n_speakers=n_speakers,
        emotion_embedding=emotion_embedding,
        **hps_ms.model)
    _ = net_g_ms.eval()
    utils.load_checkpoint(model, net_g_ms)
    
    length_scale, vits_text = get_label_value(
        vits_text, 'LENGTH', 1, 'length scale')
    noise_scale, vits_text = get_label_value(
        vits_text, 'NOISE', 0.667, 'noise scale')
    noise_scale_w, vits_text = get_label_value(
        vits_text, 'NOISEW', 0.8, 'deviation of noise')
    cleaned, vits_text = get_label(vits_text, 'CLEANED')

    stn_tst = get_text(vits_text, hps_ms, cleaned=cleaned)
    
    speaker_id = 0

    with no_grad():
        x_tst = stn_tst.unsqueeze(0)
        x_tst_lengths = torch.LongTensor([stn_tst.size(0)])
        sid = torch.LongTensor([speaker_id])
        x_tst = x_tst.to(device)
        x_tst_lengths = x_tst_lengths.to(device)
        sid = sid.to(device)
        net_g_ms = net_g_ms.to(device)
        audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale,
                                noise_scale_w=noise_scale_w, length_scale=length_scale)[0][0, 0].data.cpu().float().numpy()
        
    normalized_audio = audio / np.max(np.abs(audio))
    audio_int16 = (normalized_audio * (2**15 - 1)).astype(np.int16)
    
    return audio_int16
    
def talk(audio):
    sample_width = 2
    channels = 1
    frame_rate = 22050
    
    audio_segment = AudioSegment(
        audio.tobytes(),
        sample_width=sample_width,
        frame_rate=frame_rate,
        channels=channels
    )
    
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pa.get_format_from_width(audio_segment.sample_width),
                    channels=audio_segment.channels,
                    rate=audio_segment.frame_rate,
                    output=True)
    
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
    
def azure_tts(text):
    speech_config = speechsdk.SpeechConfig(subscription = azure_key, region = azure_region)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker = True)

    speech_config.speech_synthesis_voice_name='zh-CN-XiaoyiNeural'
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesizer.speak_text_async(text).get()