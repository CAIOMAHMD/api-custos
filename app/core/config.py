import os
import os
from dotenv import load_dotenv

load_dotenv()

SUBSCRIPTIONS = os.getenv("SUBSCRIPTIONS").split(",")

