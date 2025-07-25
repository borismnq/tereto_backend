from dotenv import load_dotenv
from google.cloud.firestore_v1 import AsyncClient

load_dotenv()

# db = firestore.Client()
db = AsyncClient()