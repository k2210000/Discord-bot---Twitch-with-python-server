import requests
import json
import os

# 讀取 config.json
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")

try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ 找不到 config.json，請確認腳本放在一起。")
    exit(1)

TWITCH_CLIENT_ID = config["twitch"]["client_id"]
TWITCH_CLIENT_SECRET = config["twitch"]["client_secret"]

def get_app_token():
    res = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    return res.json().get("access_token")

def get_user_logins(user_ids, token):
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    ids_query = "&".join(f"id={uid}" for uid in user_ids)
    res = requests.get(f"https://api.twitch.tv/helix/users?{ids_query}", headers=headers)
    data = res.json().get("data", [])
    id_to_login = {user["id"]: user["login"] for user in data}
    return id_to_login

def list_webhooks():
    token = get_app_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    res = requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers)
    data = res.json()
    
    subscriptions = data.get("data", [])
    if not subscriptions:
        print("⚠️ 沒有任何 EventSub 訂閱。")
        return

    print(f"✅ 目前共 {len(subscriptions)} 個訂閱：\n")
    
    user_ids = [sub.get("condition", {}).get("broadcaster_user_id") for sub in subscriptions]
    id_to_login = get_user_logins(user_ids, token)

    for sub in subscriptions:
        user_id = sub.get("condition", {}).get("broadcaster_user_id", "N/A")
        login = id_to_login.get(user_id, "未知使用者")
        status = sub.get("status", "unknown")
        type_ = sub.get("type", "unknown")
        callback = sub.get("transport", {}).get("callback", "N/A")
        print(f"🔹 帳號: {login} | 類型: {type_} | 狀態: {status} | ID: {user_id} | 回呼: {callback}")

if __name__ == "__main__":
    list_webhooks()
