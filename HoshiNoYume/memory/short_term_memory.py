from langchain.memory import ChatMessageHistory


class ChatShortMemory(ChatMessageHistory):
    
    def window_buffer_message(self, round: int):
        if len(self.messages) < round * 2:
            return self.messages
        else:
            return self.messages[len(self.messages) - round * 2:]

short_memory = ChatShortMemory()
