import os
import requests
# 必要的api
# openai api的KEY
openai_key = "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"
# pineconde的相关设置
pinecone_key = "a224fb88-2fb0-4c68-a36d-c064cce92985"
pinecone_env = "asia-northeast1-gcp"
pinecone_index = "yume"
# 高德地图api的key
amap_key = "616d19a5024d9b628aeb87ff02d7d91a"
# 有道云api的key
youdao_Id = "3d8de41c5b757ff9"
youdao_key = "EY42IaiboNtXryKKe761BNCtovep9aCv"
# 基本设定，进一步设定请更改各模块prompts内容
ai_name = "星野爱"
ai_language = "Japanese"    #ai说的语言，因为已有对话会载入数据库并对以后所有对话产生影响，故建议在使用前只更改一次
user_name = "xuanxuanQAQ"
user_address = "陕西省西安市西安理工大学金花校区"   # 你所在的地址，用于查找天气和周边地区
debug_mode = True       # 显示一些用于debug的信息
Streaming_enabled = True   # 文本流式显示开关，若关闭则自动开启翻译

# 可选的api（推荐）
# porcupine api的key，用于关键词唤醒
porcupine_key = "+pqxUZWf8LgRiW5hNViGcpCr/b8gQp9evS76mJDyX9I6aOOOUzIvZA=="
# 腾讯云api的ID和key，用于语音识别
tencent_Id = "AKIDSimgXFl480sdARUN7pYAYt65qMc2FJCr"
tencent_key = "YrthHenr11kDQPBvVt51jHat3xax4uUr"
# serper api，用于信息搜索（即google一下）
serper_api_key = "a9fbed79ec3094b581875f44a4c8f1215fa8f81c"
# azure api，用于azure tts
azure_key = "fc281b276b4146c2b6b983dcd544de07"
azure_region = "eastasia"
# clueai api，用于search agent0
clueai_api = "iH1deuuficStxmJuDv7hW1011011000100"

#一些相关功能
# tts相关，只能开启一个
vits_tts_enabled = True        # vits tts
azure_tts_enabled = False       # azure tts
# Live2D相关
Live2D_enabled = True
# 物联网相关
IoT_enabled = False
mqtt_broker = "82.157.235.69"
mqtt_port = 1883
openai_key_for_iot = "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"

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
