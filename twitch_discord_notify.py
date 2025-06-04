import requests
import json
import os
import subprocess
import threading
import time
import hashlib
from flask import Flask, request
from http.client import RemoteDisconnected

app = Flask(__name__)

# === 基本設定 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

MENTION_ID = config.get("mention_user_id", "")
TWITCH_CLIENT_ID = config["twitch"]["client_id"]
TWITCH_CLIENT_SECRET = config["twitch"]["client_secret"]
TARGETS = config["targets"]

NGROK_PATH = os.path.join(current_dir, "Ngrok", "ngrok.exe")
NGROK_PORT = 5000

ngrok_process = None
ngrok_url = ""
app_token = ""

def load_live_state():
    if not os.path.exists("live_state.json"):
        return {}
    with open("live_state.json", "r", encoding="utf-8") as f:
        return json.load(f)

live_messages = load_live_state()

event_cache = {}
CACHE_TTL = 600

def is_duplicate_event(data):
    key = hashlib.sha1(str(data).encode()).hexdigest()
    now = time.time()
    if key in event_cache and now - event_cache[key] < CACHE_TTL:
        return True
    event_cache[key] = now
    return False

def get_ngrok_url():
    try:
        res = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = res.json()["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except:
        return None

def start_ngrok():
    global ngrok_process
    if ngrok_process:
        ngrok_process.kill()
    ngrok_process = subprocess.Popen([
        "start", "", NGROK_PATH, "http", str(NGROK_PORT)
    ], shell=True)
    time.sleep(3)
    return get_ngrok_url()


def get_app_token():
    res = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    return res.json().get("access_token")

def delete_all_webhooks(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    res = requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers)
    for sub in res.json().get("data", []):
        requests.delete(f"https://api.twitch.tv/helix/eventsub/subscriptions?id={sub['id']}", headers=headers)

def get_user_info(token, username):
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    res = requests.get("https://api.twitch.tv/helix/users", headers=headers, params={"login": username})
    data = res.json().get("data")
    return data[0] if data else None

def get_stream_info(user_id):
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    res = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params={"user_id": user_id})
    data = res.json().get("data")
    return data[0] if data else None

def save_live_state():
    with open("live_state.json", "w", encoding="utf-8") as f:
        json.dump(live_messages, f, ensure_ascii=False, indent=2)

def monitor_viewers(streamer, user_id):
    info = live_messages.get(streamer)
    if not info:
        print(f"⚠️ 找不到 {streamer} 的 live info，結束監控")
        return

    retry_count = 0
    MAX_RETRIES = 3

    while True:
        stream = get_stream_info(user_id)
        if not stream:
            # 🔴 關台處理
            data = {
                "embeds": [
                    {
                        "author": {
                            "name": f"{info['nickname']} has ended the stream",
                            "icon_url": info['avatar']
                        },
                        "title": "🔴 已關台",
                        "color": 0xff0000
                    }
                ]
            }
            try:
                requests.patch(info["webhook_url"], json=data)
            except (requests.exceptions.RequestException, RemoteDisconnected) as e:
                print(f"❌ Discord webhook 編輯失敗（關台）：{type(e).__name__}: {e}")

            if streamer in live_messages:
                del live_messages[streamer]
                save_live_state()
            else:
                print(f"⚠️ 嘗試刪除 {streamer} 時已不存在")

            break

        # 🟢 線上狀態：每分鐘更新資料
        viewers = stream.get("viewer_count", 0)
        game = stream.get("game_name", "Unknown")
        title = stream.get("title", "無標題")
        thumbnail = stream.get("thumbnail_url", "").replace("{width}", "640").replace("{height}", "360") + f"?t={int(time.time())}"

        if info.get("last_game") != game:
            info["last_game"] = game
        if info.get("last_title") != title:
            info["last_title"] = title

        data = {
            "embeds": [
                {
                    "author": {
                        "name": f"{info['nickname']} is live now",
                        "icon_url": info['avatar']
                    },
                    "title": title,
                    "url": f"https://twitch.tv/{streamer}",
                    "description": f"🟢 開台中\nGame: {game}\nViewers: {viewers}",
                    "color": 0x00ff00,
                    "image": {"url": thumbnail}
                }
            ]
        }

        try:
            requests.patch(info["webhook_url"], json=data)
            retry_count = 0  # 成功就重置
        except (requests.exceptions.RequestException, RemoteDisconnected) as e:
            retry_count += 1
            print(f"❌ Discord webhook 編輯失敗（第 {retry_count} 次）：{type(e).__name__}: {e}")
            if retry_count >= MAX_RETRIES:
                print(f"⚠️ 超過重試上限，移除 {streamer} 並停止監控")
                if streamer in live_messages:
                    del live_messages[streamer]
                    save_live_state()
                break
            else:
                time.sleep(5)
                continue

        save_live_state()
        time.sleep(60)

def handle_stream_online(stream_info):
    streamer = stream_info["user_login"]
    user_id = stream_info["user_id"]
    game = stream_info.get("game_name", "Unknown")
    viewers = stream_info.get("viewer_count", 0)
    thumbnail = stream_info.get("thumbnail_url", "").replace("{width}", "640").replace("{height}", "360") + f"?t={int(time.time())}"
    title = stream_info.get("title", "無標題")

    for target in TARGETS:
        if target["twitch_username"].lower() == streamer.lower():
            nickname = target.get("nickname", streamer)
            avatar = get_user_info(app_token, streamer)["profile_image_url"]
            embed = {
                "author": {
                    "name": f"{nickname} is live now",
                    "icon_url": avatar
                },
                "title": title,
                "url": f"https://twitch.tv/{streamer}",
                "description": f"🟢 開台中\nGame: {game}\nViewers: {viewers}",
                "color": 0x00ff00,
                "image": {"url": thumbnail}
            }
            webhook_data = {
                "content": f"<@{MENTION_ID}>" if MENTION_ID else "",
                "embeds": [embed]
            }

            webhook_url = target["discord_webhook"] + "?wait=true"
            res = requests.post(webhook_url, json=webhook_data)

            try:
                msg = res.json() if res.text else {}
                message_id = msg.get("id")
                message_url = f"{target['discord_webhook']}/messages/{message_id}" if message_id else None
            except:
                message_id = None
                message_url = None

            if message_url:
                live_messages[streamer] = {
                    "message_id": message_id,
                    "webhook_url": message_url,
                    "nickname": nickname,
                    "avatar": avatar,
                    "last_game": game,
                    "last_title": title,
                    "start_time": time.time()
                }
                save_live_state()
                threading.Thread(target=monitor_viewers, args=(streamer, user_id), daemon=True).start()

@app.route("/twitch", methods=["POST"])
def twitch_webhook():
    payload = request.json
    headers = request.headers

    if headers.get("Twitch-Eventsub-Message-Type") == "webhook_callback_verification":
        return payload["challenge"], 200

    if is_duplicate_event(payload):
        print("⚠️ 重複事件，略過")
        return "", 200

    if payload.get("subscription", {}).get("type") == "stream.online":
        event = payload["event"]
        user_id = event["broadcaster_user_id"]
        stream_info = get_stream_info(user_id)
        if stream_info:
            handle_stream_online(stream_info)

    return "", 204

@app.route("/reload", methods=["POST"])
def manual_reload():
    global app_token
    print("🔁 接收到 reload 指令")
    app_token = get_app_token()
    delete_all_webhooks(app_token)
    subscribe_webhooks(app_token, ngrok_url)
    scan_current_live_users()
    return "ok", 200

def subscribe_webhooks(token, callback_url):
    for target in TARGETS:
        info = get_user_info(token, target["twitch_username"])
        user_id = info["id"]
        target["user_id"] = user_id
        target["avatar"] = info["profile_image_url"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": TWITCH_CLIENT_ID,
            "Content-Type": "application/json"
        }
        data = {
            "type": "stream.online",
            "version": "1",
            "condition": {"broadcaster_user_id": user_id},
            "transport": {
                "method": "webhook",
                "callback": f"{callback_url}/twitch",
                "secret": "dummysecret"
            }
        }
        res = requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers, json=data)
        if res.status_code == 202:
            print(f"✅ 成功訂閱 {target['twitch_username']}")
        else:
            print(f"❌ 訂閱 {target['twitch_username']} 失敗: {res.status_code}")

def scan_current_live_users():
    print("🔍 啟動時掃描目前已開台實況主...")
    for target in TARGETS:
        user_id = target.get("user_id")
        if not user_id:
            continue
        stream = get_stream_info(user_id)
        if stream:
            streamer = target["twitch_username"]
            if streamer in live_messages:
                print(f"🟢 已存在訊息，啟動監控 {streamer}")
                threading.Thread(target=monitor_viewers, args=(streamer, user_id), daemon=True).start()
            else:
                handle_stream_online(stream)

def after_flask_ready():
    global app_token
    print("✅ 取得 Twitch Token...")
    app_token = get_app_token()
    delete_all_webhooks(app_token)
    subscribe_webhooks(app_token, ngrok_url)
    scan_current_live_users()

if __name__ == "__main__":
    print("✅ 啟動 ngrok 中...")
    ngrok_url = start_ngrok()
    print(f"🌐 ngrok URL: {ngrok_url}")

    threading.Thread(target=lambda: app.run(port=NGROK_PORT), daemon=True).start()
    time.sleep(3)
    after_flask_ready()
    print("✅ 等待 webhook 中...")

    while True:
        time.sleep(1)
