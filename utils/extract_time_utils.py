# Prompt for extracting time interval
from langchain.chains.llm import LLMChain

from llm.llm_config import llm
from prompts.PromptAI import extract_time_prompt

extract_time_chain = LLMChain(llm=llm, prompt=extract_time_prompt)


async def extract_time(message: str) -> str:
    result = await extract_time_chain.arun(message=message)
    return result.strip()
