import paho.mqtt.client as mqtt
from api_key import *
import json
import threading

topic = "/moon_light"
light_property = {
    "switch": "",
    "color": "",
}
client = None

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


def mqtt_publish(publish_message: dict[str, str]):
    publish_message = json.dumps(publish_message)
    client.publish(topic, publish_message)

            
if IoT_enabled:
    thread_mqtt = threading.Thread(target=mqtt_connect)  # 初始化MQTT
    thread_mqtt.start()