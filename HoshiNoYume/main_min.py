from api_key import *
import perception
import thinking
import memory

def main():
    while True:
        user_words = perception.text_input()    #文字输入
        memory.short_memory.add_user_message(user_words)
        response = thinking.chat(memory.short_memory)
        memory.short_memory.add_ai_message(response)
        
if __name__ == '__main__':
    main()