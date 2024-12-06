from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
import config

class WrappedChatOpenAI:
    def __init__(self, llm):
        self.llm = llm 

    def __getattr__(self, name):

        return getattr(self.llm, name)

    def call(self, *args, **kwargs):

        if config.OPENAI_FALL_BACK:
            raise ValueError("LLM FALL BACK ERROR")
        
        return self.llm.call(*args, **kwargs)

    def generate(self, *args, **kwargs):

        if config.OPENAI_FALL_BACK:
            raise ValueError("LLM FALL BACK ERROR")

        return self.llm.generate(*args, **kwargs)
    
    def invoke(self, *args, **kwargs):

        if config.OPENAI_FALL_BACK:
            raise ValueError("LLM FALL BACK ERROR")

        return self.llm.invoke(*args, **kwargs)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# llm=WrappedChatOpenAI(llm)
