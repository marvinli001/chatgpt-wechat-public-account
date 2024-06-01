import os
import openai
import werobot
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for
from werobot.contrib.flask import make_view

load_dotenv()

robot = werobot.WeRoBot(token=os.getenv("WECHAT_TOKEN"))

openai.api_key = os.getenv("OPENAI_API_KEY")

max_tokens = os.getenv("MAX_TOKENS")
max_tokens = 100 if max_tokens is None else int(max_tokens)

# 预设密文
ACTIVATION_CODE = os.getenv("ACTIVATION_CODE")

# 初始化白名单
authorized_users = set()

# 白名单文件路径
WHITELIST_FILE = 'whitelist.txt'

# 加载白名单
def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return set()
    with open(WHITELIST_FILE, 'r') as file:
        return set(line.strip() for line in file.readlines())

# 保存白名单
def save_whitelist(whitelist):
    try:
        with open(WHITELIST_FILE, 'w') as file:
            for item in whitelist:
                file.write(f"{item}\n")
        print(f"Whitelist saved successfully: {whitelist}")
    except Exception as e:
        print(f"Error saving whitelist: {e}")

# 加载白名单到内存中
authorized_users = load_whitelist()
print(f"Loaded whitelist: {authorized_users}")

app = Flask(__name__)

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

def split_message(message, limit=200):
    """将长消息按指定长度分割成多段"""
    return [message[i:i + limit] for i in range(0, len(message), limit)]

@robot.handler
def handle_message(message):
    wxid = message.source
    user_message = message.content.strip()
    
    # 检查用户是否在白名单中
    if wxid in authorized_users:
        reply = get_gpt3dot5_reply(user_message)
        reply_segments = split_message(reply)
    else:
        # 检查用户是否输入激活码
        if user_message == ACTIVATION_CODE:
            authorized_users.add(wxid)
            save_whitelist(authorized_users)
            reply_segments = ["You have been authorized."]
        else:
            reply_segments = ["You are not authorized. Please log in first."]
    
    # 返回分段消息
    return "\n".join(reply_segments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        wxid = request.form['wxid']  # 获取微信用户ID
        if password == ACTIVATION_CODE:
            authorized_users.add(wxid)
            save_whitelist(authorized_users)
            return redirect(url_for('index'))
        else:
            return 'Invalid password'
    return '''
        <form method="post">
            WeChat ID: <input type="text" name="wxid">
            Password: <input type="password" name="password">
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/logout', methods=['POST'])
def logout():
    wxid = request.form['wxid']  # 获取微信用户ID
    if wxid in authorized_users:
        authorized_users.remove(wxid)
        save_whitelist(authorized_users)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return 'Welcome to the WeChat GPT integration!'

# 将 WeRoBot 挂载到 Flask 上
app.add_url_rule(rule='/robot/', 
                 endpoint='werobot', 
                 view_func=make_view(robot),
                 methods=['GET', 'POST'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
