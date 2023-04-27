import os
# 腾讯云api的ID和KEY
tencent_Id = "xxxxxxxxxxxxxxxxxxx"
tencent_key = "xxxxxxxxxxxxxxxxxxx"
# 和风天气api的KEY
city_location = "101110109"
Qweather_key = "xxxxxxxxxxxxxxxxxxx"
# openai api的KEY
openai_key = "sk-xxxxxxxxxxxxxxxxxxx"
# 有道云api的KEY
youdao_Id = "xxxxxxxxxxxxxxxxxxx"
youdao_key = "xxxxxxxxxxxxxxxxxxx"
# porcupine api的key
porcupine_key = "xxxxxxxxxxxxxxxxxxx"
# 项目目录的地址
script_dir = os.path.dirname(os.path.abspath(__file__))
# vits模型地址，一般不用改
vits_model_path = os.path.join(script_dir, 'model', 'tts', 'G_latest.pth')
vits_config_path = os.path.join(
    script_dir, 'model', 'tts', 'moegoe_config.json')
# porcupine的模型地址，一般不用改
porcupine_model = os.path.join(
    script_dir, 'model', 'kws', 'Hey-Dream_en_windows_v2_2_0.ppn')
# 物联网相关
IoT_enabled = False
mqtt_broker = "xxx.xxx.xxx.xxx"
mqtt_port = 1883
openai_key_for_iot = "sk-xxxxxxxxxxxxxxxxxxx"
# Live2D相关
Live2D_enabled = False
