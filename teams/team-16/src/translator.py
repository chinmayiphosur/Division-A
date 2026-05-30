import os
from langchain_core.prompts import PromptTemplate

class FIRTranslator:
    def __init__(self, fallback_llm_provider="gemini"):
        self.fallback_llm_provider = fallback_llm_provider
        self.fallback_llm = None
        self._init_fallback_llm()

    def _init_fallback_llm(self):
        if self.fallback_llm_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            self.fallback_llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key, temperature=0.1)

    def _fallback_translate(self, text: str, target_language: str) -> str:
        prompt = PromptTemplate(
            template="You are a professional legal translator. Translate the following plain-English legal narrative into {target_language}. Maintain an 8th-grade reading level. Only return the translated text.\n\n{text}",
            input_variables=["target_language", "text"]
        )
        return (prompt | self.fallback_llm).invoke({"target_language": target_language, "text": text}).content

    def translate_to_hindi(self, text: str) -> str:
        return self._fallback_translate(text, "Hindi")

    def translate_to_kannada(self, text: str) -> str:
        return self._fallback_translate(text, "Kannada")
