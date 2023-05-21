from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import StringPromptTemplate
from langchain import OpenAI, LLMChain
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish
import re
from actions.interact import interact_tools
import time
from thinking.prompts import AGENT_INTERACT_PROMPTS_TEMPLATE
from api_key import debug_mode , formatted_address


# 设置agent的prompts的模板类
class CustomPromptTemplate(StringPromptTemplate):
    # 使用的template文本模板
    template: str
    # 可使用的工具
    tools: List[Tool]
    
    def format(self, **kwargs) -> str:
        # 获取当前时间
        current_time = time.time()
        local_time = time.localtime(current_time)
        formatted_time = time.strftime("%Y-%m-%d", local_time)
        # 获取中间步骤 (AgentAction, Observation tuples)
        # 将模板格式化为常规形式，即带入变量
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        kwargs["time"] = formatted_time
        kwargs["location"] = formatted_address
        return self.template.format(**kwargs)
    
tools = interact_tools

prompt = CustomPromptTemplate(
    template=AGENT_INTERACT_PROMPTS_TEMPLATE,
    tools=tools,
    # 这里不用带入agent_scratchpad`,`tools`和`tool_names`三个变量，因为在上面format方法中已经带入了
    # 添加可带入的prompts变量
    input_variables=["input", "intermediate_steps"]
)

# agent输出解析,一般情况下用不到
class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # 查看agent是否该结束
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # 解析action和action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # 返回action和action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
output_parser = CustomOutputParser()

llm = OpenAI(temperature=0)
# 由LLM模型和prompt构成llm_chain
llm_chain = LLMChain(llm=llm, prompt=prompt)
tool_names = [tool.name for tool in tools]
# 由llm_chain和tools构成agent
agent = LLMSingleActionAgent(
    llm_chain=llm_chain, 
    output_parser=output_parser,
    stop=["\nObservation:"], 
    allowed_tools=tool_names
)
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=debug_mode)

def agent_interact(user_words):
    return agent_executor.run(user_words)