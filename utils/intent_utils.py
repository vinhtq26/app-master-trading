import json

from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from prompts.PromptAI import intent_prompt

from llm.llm_config import llm


# Define prompts template


async def classify_intent(message: str) -> str:
    """
    Classify the intent of a given message using the LLM.

    Args:
        message (str): The input message to classify.

    Returns:
        str: The classified intent.
    """
    # Initialize LLM chain
    intent_chain = LLMChain(llm=llm, prompt=intent_prompt)
    result = await intent_chain.arun(message=message)
    return result.strip()