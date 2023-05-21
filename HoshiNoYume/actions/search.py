import requests
from api_key import *
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
import requests
import time


# 把搜索工具写在这里
# 查找当前天气
def search_current_weather(_):
    print("少女搜索中...")
    queryurl = f"https://restapi.amap.com/v3/weather/weatherInfo?key={amap_key}&city={amap_adcode}"
    
    response = requests.get(queryurl)
    res_json = response.json()
    res = res_json['lives'][0]
    # 去除无关属性
    res.pop('province', None)
    res.pop('city', None)
    res.pop('adcode', None)
    res.pop('reporttime', None)
    
    return res

# 检索当前确切时间
def current_accurate_time(_):
    print("少女搜索中...")
    current_time = time.time()
    local_time = time.localtime(current_time)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    
    return formatted_time
    

# 谷歌搜索
search = GoogleSerperAPIWrapper()
def google_search(question):
    print("少女搜索中...")
    return search.run(question)

# 百度地图周边信息搜索
def place_search(keywords):
    print("少女搜索中...")
    radius = 2000   #搜索半径，单位m
    queryurl = f"https://restapi.amap.com/v5/place/around?key={amap_key}&keywords={keywords}&location={amap_location}&radius={radius}"
    
    response = requests.get(queryurl)
    response_json = response.json()
    res = response_json['pois']
    # 去除无关属性
    for i in range(len(res)):
        res[i].pop('parent', None)
        res[i].pop('pcode', None)
        res[i].pop('adcode', None)
        res[i].pop('pname', None)
        res[i].pop('cityname', None)
        res[i].pop('typecode', None)
        res[i].pop('adname', None)
        res[i].pop('citycode', None)
        res[i].pop('location', None)
        res[i].pop('id', None)  
    
    return res
    
# 只是聊聊天捏，这里做二次筛选
def just_chat(_):
    return "None"

# 搜索工具列表
search_tools = [
    Tool(
        name = "Search",
        func=google_search,
        description="Only use this when you need to answer questions about current events",
        return_direct=False
    ),
    Tool(
        name = "Weather",
        func=search_current_weather,
        description="Use this to retrieve the current weather.",
        return_direct=True
    ),
    Tool(
        name = "Place Search",
        func=place_search,
        description="Use this to search for nearby locations.Input a only single keyword like 'restaurant'.",
        return_direct=True
    ),
    Tool(
        name = "Accurate time",
        func=current_accurate_time,
        description="Use this to get the current accurate time.",
        return_direct=False
    ),
    Tool(
        name = "Chat",
        func=just_chat,
        description="If you think I'm not asking a question or you don't need to use other tools or i'm instruct you to do something, take this",
        return_direct=True
    )
]