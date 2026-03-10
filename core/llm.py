from langchain_openai import ChatOpenAI
from config.settings import settings

def chat(model: str = 'gpt-4o-mini', temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature, api_key=settings.OPENAI_API_KEY)