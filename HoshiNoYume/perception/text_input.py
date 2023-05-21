from api_key import user_name
import time

def text_input():
    user_input = input(user_name + ": ")
    # 加上时间戳
    current_time = time.time()
    local_time = time.localtime(current_time)
    formatted_time = time.strftime("%Y-%m-%d %H:%M", local_time)
    
    user_input = f'({formatted_time})' + user_input
    
    return user_input