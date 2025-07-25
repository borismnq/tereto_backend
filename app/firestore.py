import os
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

db = firestore.Client()