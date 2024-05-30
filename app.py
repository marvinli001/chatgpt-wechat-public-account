import os
import openai
import requests
import werobot
from dotenv import load_dotenv
from flask import Flask, request
from werobot.contrib.flask import make_view

load_dotenv()

robot = werobot.WeRoBot(token=os.getenv("WECHAT_TOKEN"))

openai.api_key = os.getenv("OPENAI_API_KEY")

max_tokens = os.getenv("MAX_TOKENS")
max_tokens = 100 if max_tokens is None else int(max_tokens)

def get_gpt3_reply(text):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        max_tokens=max_tokens,
        temperature=0,
    )
    return response.choices[0].text.strip()

def get_gpt3dot5_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {"role": "user", "content": text}
        ],
        max_tokens=max_tokens,
        temperature=0.8
    )
    return response.choices[0].message.content.strip()

@robot.handler
def handle_message(message):
    if message.type == 'image':
        return handle_image(message)
    elif message.type == 'text':
        return handle_text(message)
    else:
        return 'Unsupported message type.'

def handle_text(message):
    if os.getenv("GPT_MODEL_VERSION") == "3":
        reply = get_gpt3_reply(message.content)
    else:
        reply = get_gpt3dot5_reply(message.content)

    return reply

def handle_image(message):
    image_url = message.img
    response = process_image_with_openai(image_url)
    return response

def process_image_with_openai(image_url):
    # 由于当前API不支持图像处理，这里仅返回图片的URL
    # 在未来使用OpenAI Vision模型时，可直接替换此部分代码
    return f'Processed image URL: {image_url}'

# Integrate with Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Web App with Python Flask!'

app.add_url_rule(rule='/robot/',  # WeRoBot 的绑定地址
                endpoint='werobot',  # Flask 的 endpoint
                view_func=make_view(robot),
                methods=['GET', 'POST'])

if __name__ == "__main__":
    port = os.getenv("PORT")
    port = 8888 if port is None else int(port)
    app.run(host='0.0.0.0', port=port)
