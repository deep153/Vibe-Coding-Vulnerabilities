import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import google.generativeai as genai

load_dotenv()

MODELS = [
    {"provider": "openai", "model": "gpt-5.2"},
    {"provider": "anthropic", "model": "claude-sonnet-4-5-20250929"},
    {"provider": "google", "model": "gemini-3.1-pro-preview"}
]

def test_models():
    print("Starting Model Connectivity Test...")
    
    for m in MODELS:
        provider = m["provider"]
        model = m["model"]
        print(f"\nTesting {provider.upper()} model: {model}")
        
        try:
            if provider == "openai":
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print(f"✅ Success! Response: {response.choices[0].message.content}")

            elif provider == "anthropic":
                client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                response = client.messages.create(
                    model=model,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                print(f"✅ Success! Response: {response.content[0].text}")

            elif provider == "google":
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                model_instance = genai.GenerativeModel(model)
                response = model_instance.generate_content("Hello")
                print(f"✅ Success! Response: {response.text}")

        except Exception as e:
            print(f"❌ Failed: {str(e)}")

if __name__ == "__main__":
    test_models()

