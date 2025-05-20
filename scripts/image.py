from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",  # Use GPT-4o, which handles vision
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image and why do you think that?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://www.gpa26.com/2868170-medium_default/washer-fluid-reservoir-tank-volvo-v70-i-ph2-30649920-s0-8192a.jpg"
                    },
                },
            ],
        }
    ],
)

print(response.choices[0].message.content)
