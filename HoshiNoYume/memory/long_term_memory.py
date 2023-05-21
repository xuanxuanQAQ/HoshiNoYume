import pinecone
import openai
from api_key import openai_key , pinecone_key , ai_name , user_name , pinecone_env , pinecone_index
from langchain.memory.summary import SummarizerMixin
from langchain.llms import OpenAI
from memory.prompts import SUMMARY_PROMPT
from typing import Any, Optional
from memory.short_term_memory import ChatShortMemory
import time

class ChatLongMemory(SummarizerMixin):
    index : Optional[Any] = None
    summary_memory : str = ""
    def init(self):
        openai.api_key = openai_key
        pinecone.init(api_key=pinecone_key, environment=pinecone_env)
        self.index = pinecone.Index(pinecone_index)
        with open("HoshiNoYume\memory\long_summary_memory.txt", "r") as file:
            self.summary_memory = file.read()

    def vector_write(self,text):
        response = openai.Embedding.create(
            input=text,
            model="text-similarity-babbage-001"
        )
        self.index.upsert(
             vectors=[
                {'id':'vec1', 
                'values':response['data'][0]['embedding'], 
                'metadata':{'genre': 'drama'},
                'sparse_values':
                {'indices': [10, 45, 16],
                'values':  [0.5, 0.5, 0.2]}}
            ])
    
    def short_memory_vector_write(self,short_memory:ChatShortMemory):
        # 把短期记忆的对话记录写进向量数据库
        for i in range(len(short_memory.messages)//2):
            written_str = short_memory.messages[2*i].content + "&" + short_memory.messages[2*i+1].content
            vector = openai.Embedding.create(
                input=written_str,
                model="text-embedding-ada-002"
            )
            
            current_time = time.time()
            local_time = time.localtime(current_time)
            formatted_time = time.strftime("%Y%m%d%H%M%S", local_time)
            
            self.index.upsert(
                vectors=[
                    {'id':formatted_time, 
                    'values':vector['data'][0]['embedding'], 
                    'metadata':{'human': short_memory.messages[i].content,
                                'ai': short_memory.messages[i+1].content},
                    }
                ])
            
    def vector_search(self,text):
        openai.api_key = openai_key
        vector = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        response = self.index.query(
            vector=vector['data'][0]['embedding'], 
            top_k=5, 
            include_values=False,
            include_metadata=True)
        return response
        
    def summary_write(self,short_memory:ChatShortMemory):
        messages = short_memory.messages
        self.summary_memory = self.predict_new_summary(messages,self.summary_memory)
        with open("HoshiNoYume\memory\long_summary_memory.txt", "w") as file:
            file.write(self.summary_memory)
        return self.summary_memory
        
long_memory = ChatLongMemory(llm=OpenAI(temperature=0),
                             ai_prefix=ai_name,
                             human_prefix=user_name,
                             prompt=SUMMARY_PROMPT)
long_memory.init()