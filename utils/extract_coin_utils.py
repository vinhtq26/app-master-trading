import json

from langchain.chains.llm import LLMChain

from llm.llm_config import llm
from prompts.PromptAI import extract_coin_template


# extract coin
async def extractCoin(message: str, coinlist: list):
    chain = LLMChain(llm=llm, prompt=extract_coin_template)

    response = chain.run(message=message, coin_list=", ".join(coinlist))

    try:
        return json.loads(response)
    except:
        return []