from LLM import LLMProcessor
from streamlit_app import texts
from dotenv import load_dotenv
from openai import OpenAI
import os

# Initialize LLM processor with your API key
load_dotenv()
api_key = os.getenv("API_KEY")
llm = LLMProcessor(api_key)

# Generate the test procedure
test_procedure = llm.generate_test_procedure(texts)

# Print the result
print("===== Generated Test Procedure =====")
print(test_procedure)

