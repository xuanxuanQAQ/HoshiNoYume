from api_key import *
import perception
import thinking
import memory
import tools
import actions
import threading
import re

# 初始化
def init():
    tools.print_device_info()
    if Live2D_enabled:
        thread_socket = threading.Thread(target=actions.socket_init)  # 初始化MQTT
        thread_socket.start()
        actions.live2d_open()
        thread_socket.join()
    tools.press_key_wake_up()

# 结束对话
def conv_end():
    # 整理此次对话
    memory.long_memory.summary_write(memory.short_memory)
    memory.long_memory.short_memory_vector_write(memory.short_memory)
    # 等待开启下次对话
    tools.press_key_wake_up()
    
def main():
    init()
    while True:
        user_words = perception.text_input()    #文字输入
        # user_words = perception.listen()      #语音输入
        search_info = thinking.agent_search(user_words)
        memory.short_memory.add_user_message(user_words)
        response = thinking.chat(memory.short_memory, memory.long_memory, search_info)
        memory.short_memory.add_ai_message(response)
        
        interact = re.search(r'#interact:\s*(.*?)\)', response)
        if interact == "end":
            conv_end()
        else:
            thinking.agent_interact(interact)
        
if __name__ == '__main__':
    main()