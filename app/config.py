import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_KEY = os.getenv("OPENAI_API_KEY")
    FAISS_INDEX_PATH = "data/faiss_index/index.faiss"
    FAISS_DIRECTORY = "data/faiss_index"
    TEXT_MAPPING_PATH = "data/faiss_index/index.pkl"

settings = Settings()
