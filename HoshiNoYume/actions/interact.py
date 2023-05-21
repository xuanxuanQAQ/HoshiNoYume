from actions.IoT_control import mqtt_publish
from langchain.agents import Tool
from api_key import *

def light_handle(instruction):
    print("少女行动中...")
    if "on" in instruction:
        message = {"switch": "light on"}
    elif "off" in instruction:
        message = {"switch": "light off"}
    mqtt_publish(message)

def end_talk(_):
    print("结束对话捏...")
    return "end"

def just_chat(_):
    return "chat"
    

# 操作工具列表
interact_tools = [
    Tool(
        name = "Light Handle",
        func=light_handle,
        description="Use this to control the light, input 'on' to turn on the light, and input 'off' to turn off the light.",
        return_direct=True
    ),
    Tool(
        name = "end conversation",
        func=end_talk,
        description="If you think it's time to end conversation, use this.",
        return_direct=True
    ),
    Tool(
        name = "Chat",
        func=just_chat,
        description="If you think I'm not asking a question or you don't need to use other tools or i'm instruct you to do something, take this",
        return_direct=True
    )
]