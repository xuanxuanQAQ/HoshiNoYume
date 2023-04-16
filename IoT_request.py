import paho.mqtt.client as mqtt
from api_key import *
import json
import openai

topic = "/moon_light"
light_property = {
    "switch": "",
    "color": "",
}


def mqtt_connect():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("连接上MQTT broker了喵~")
            client.subscribe(topic)

    # 创建mqtt实例
    global client
    client = mqtt.Client()
    # 绑定连接服务器上时的回调函数
    client.on_connect = on_connect
    # 连接broker
    client.connect(mqtt_broker, mqtt_port)
    client.loop_forever()


def mqtt_publish(text):
    openai.api_key = openai_key_for_iot
    system_set = "Please control room lights based on my upcoming words and respond using @xxx format:To turn the light on, reply with '@light on'.To turn the light off, reply with '@light off'.Follow these guidelines for processing and responding to commands.'"
    messages = [
        {"role": "system", "content": system_set},
        {"role": "user", "content": "请帮我把灯打开"},
        {"role": "assistant",
         "content": "@light on"},
        {"role": "user", "content": text}
    ]
    mqtt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.9,
        messages=messages
    )
    response_text = mqtt_response.choices[0].message.content
    if response_text.rfind('@') != -1:
        if response_text.rfind('@light on') != -1:
            publish_message = {
                "switch": "light on",
            }
            publish_message = json.dumps(publish_message)
            print("要发送的JSON消息:" + publish_message)
            client.publish(topic, publish_message)
        elif response_text.rfind('@light off') != -1:
            publish_message = {
                "switch": "light off",
            }
            publish_message = json.dumps(publish_message)
            print("要发送的JSON消息:" + publish_message)
            client.publish(topic, publish_message)
