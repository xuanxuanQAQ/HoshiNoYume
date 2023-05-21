import os
import requests
# 必要的api
# openai api的KEY
openai_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# pineconde的相关设置
pinecone_key = "xxxxxxxxxxxxxxxxxxxxxxxxx"
pinecone_env = "asia-northeast1-gcp"
pinecone_index = "yume"
# 高德地图api的key
amap_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 有道云api的key
youdao_Id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
youdao_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 基本设定，进一步设定请更改各模块prompts内容
ai_name = "星野爱"
ai_language = "Japanese"    #ai说的语言，因为已有对话会载入数据库并对以后所有对话产生影响，故建议在使用前只更改一次
user_name = "xuanxuanQAQ"
user_address = "陕西省西安市西安理工大学金花校区"   # 你所在的地址，用于查找天气和周边地区
debug_mode = True       # 显示一些用于debug的信息
text_streamingflow = True   # 文本流式显示开关

# 可选的api（推荐）
# porcupine api的key，用于关键词唤醒
porcupine_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 腾讯云api的ID和key，用于语音识别
tencent_Id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
tencent_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# serper api，用于信息搜索（即google一下）
serper_api_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# azure api，用于azure tts
azure_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
azure_region = "eastasia"
# clueai api，用于search agent0
clueai_api = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

#一些相关功能
# tts相关，只能开启一个
vits_tts_enabled = True        # vits tts
azure_tts_enabled = False       # azure tts
# Live2D相关
Live2D_enabled = True
# 物联网相关
IoT_enabled = False
mqtt_broker = "xx.xxx.xxx.xx"
mqtt_port = 1883
openai_key_for_iot = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 项目目录的地址
script_dir = os.path.dirname(os.path.abspath(__file__))
# vits模型地址，一般不用改
vits_model_path = os.path.join(script_dir, '..' , 'model', 'tts', 'G_latest.pth')
vits_config_path = os.path.join(
    script_dir, '..','model', 'tts', 'moegoe_config.json')
# porcupine的模型地址，一般不用改
porcupine_model = os.path.join(
    script_dir, '..','model', 'kws', 'Hey-Dream_en_windows_v2_2_0.ppn')

# 一些需要的信息初始化，一般不用改
# 将一些key加入环境变量
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["serper_api_key"] = serper_api_key
def get_address_info():
    queryurl = f"https://restapi.amap.com/v3/geocode/geo?key={amap_key}&address={user_address}"
    response = requests.get(queryurl)
    response = response.json()
    from tools.translate import text2text_translate
    formatted_address = text2text_translate(response['geocodes'][0]['formatted_address'] , src_lang="zh-CHS" ,target_lang="en")
    return response['geocodes'][0]['adcode'] , response['geocodes'][0]['location'] , formatted_address
amap_adcode , amap_location , formatted_address= get_address_info()
