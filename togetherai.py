from together import Together

client = Together(
    api_key="tgp_v1_zHkn_nwXBRqIzYCoZMcadV-of5XM20lyzwyM9byqRA8"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {
            "role": "user",
            "content": "What are some fun things to do in New York?"
        }
    ]
)

print(response.choices[0].message.content)