from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    AIMessage,
    HumanMessage
)
from langchain.callbacks.base import BaseCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from thinking.prompts import CHATMODEL1_SYS_PROMPTS
from memory.short_term_memory import ChatShortMemory
from memory.long_term_memory import ChatLongMemory
from api_key import *
from actions.speaking import talk , vits_tts , azure_tts
from typing import Any
import threading
import queue
import sys
import time
from tools import text2text_translate
import re

# vits语音生成队列
def vits_queue(audio_queue, text, priority):
    audio = vits_tts(text)
    audio_queue.put((priority,audio))

# 按队列播放生成后的语音
def talk_queue(audio_queue:queue.PriorityQueue):
    priority_pre = 0
    while True:
        priority, audio = audio_queue.get()
        while priority_pre != priority - 1:
            audio_queue.put((priority , audio))
            time.sleep(0.2)
            priority , audio = audio_queue.get()
        priority_pre = priority
        if audio is None:
            break
        talk(audio)
        
task_queue = queue.PriorityQueue()

# 流式传输的class
class CustomStreamingCallbackHandler(StreamingStdOutCallbackHandler):
    sentence_buffer = ""
    vits_threads = []
    parentheses_flag = False
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        token = token.replace('\n','')
        if token in '':
            return
        elif "(" in token:
            self.parentheses_flag = True
        elif ")" in token :
            self.parentheses_flag = False
            return
        if self.parentheses_flag == True:
            return
        if vits_tts_enabled:
            self.sentence_buffer += token
            if token in "。！？":
                vits_thread = threading.Thread(target=vits_queue, args=(task_queue, self.sentence_buffer, len(self.vits_threads)+1))
                vits_thread.start()
                self.vits_threads.append(vits_thread)
                self.sentence_buffer = ""
        if Streaming_enabled == True:
            sys.stdout.write(token)
            sys.stdout.flush()

def chat(short_memory:ChatShortMemory, long_memory:ChatLongMemory = None, search_info:str = "None"):
    # 创建gpt3.5turbo实例
    chat = ChatOpenAI(streaming=True, callback_manager=BaseCallbackManager([CustomStreamingCallbackHandler()]), verbose=True, temperature=0.7)
    
    # 获取当前时间
    current_time = time.time()
    local_time = time.localtime(current_time)
    formatted_time = time.strftime("%Y-%m-%d %H:%M", local_time)
    
    # 向量搜索    
    if long_memory == None:
        summary_memory = "None"
    else:
        vector_memory = long_memory.vector_search(short_memory.messages[-1].content)
        for match in vector_memory['matches']:
            human_words = match['metadata'].get('human')
            ai_words = match['metadata'].get('ai')

            if human_words is not None and ai_words is not None:
                temp_memory_message = [HumanMessage(content=human_words)] + short_memory.messages
                temp_memory_message += [AIMessage(content=ai_words)] + short_memory.messages
                
        summary_memory = long_memory.summary_memory
    
    sys_prompts = CHATMODEL1_SYS_PROMPTS.format(name=ai_name, info=search_info , time=formatted_time , locate=formatted_address, summary_memory=summary_memory, language=ai_language)
    
    temp_memory_message = [SystemMessage(content=sys_prompts)] + short_memory.messages
    
    print(ai_name + ": ", end="")
    reply_words = chat(temp_memory_message)
    response = reply_words.content
    
    if Streaming_enabled == True:
        print("")   # 换行
    else:
        text_without_brackets = re.sub(r'\(.*?\)', '', response)
        print(text2text_translate(text_without_brackets))

    if vits_tts_enabled:
        talk_thread = threading.Thread(target=talk_queue, args=(task_queue,))
        talk_thread.start()
        for vits_thread in CustomStreamingCallbackHandler.vits_threads:
            vits_thread.join()
        task_queue.put((len(CustomStreamingCallbackHandler.vits_threads)+1,None)) 
        talk_thread.join()
        CustomStreamingCallbackHandler.vits_threads = []
    elif azure_tts_enabled:
        azure_tts(response)
        
    return response