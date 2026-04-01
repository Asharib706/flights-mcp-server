from openai import OpenAI

client = OpenAI(
    base_url="http://212.18.29.192/v1",
    api_key="EMPTY"   # vLLM usually doesn't require real key
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-OCR",
    messages=[
        {"role": "user", "content": "tell me 1000 words story"}
    ]
)

print(response.choices[0].message.content)