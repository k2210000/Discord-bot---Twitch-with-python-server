import json
import os

# 取得目前程式所在資料夾
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")

# 載入現有設定
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ 找不到 config.json，請確認檔案與腳本放在一起。")
    exit(1)

def list_targets():
    print("\n🎯 目前追蹤的 Twitch 使用者：")
    for idx, target in enumerate(config["targets"], 1):
        print(f"{idx}. {target['twitch_username']}")

def save_config():
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

while True:
    print("\n=== 管理 Twitch 追蹤列表 ===")
    action = input("請輸入你要執行的動作（add / delete / exit）：").strip().lower()

    if action == "add":
        username = input("請輸入要新增的 Twitch 使用者名稱：").strip()
        if not username:
            print("❌ 錯誤：使用者名稱不能是空白！")
            continue

        default_webhook = config["targets"][0]["discord_webhook"] if config["targets"] else ""
        webhook = input(f"請輸入 Discord Webhook（直接按 Enter 使用預設）：\n{default_webhook}\n> ").strip()
        if webhook == "":
            webhook = default_webhook

        if webhook == "":
            print("❌ 錯誤：沒有找到預設 Webhook，請手動輸入！")
            continue

        config["targets"].append({
            "twitch_username": username,
            "discord_webhook": webhook
        })

        save_config()
        print(f"✅ 已成功新增 {username}！")

    elif action == "delete":
        if not config["targets"]:
            print("⚠️ 沒有任何可刪除的目標。")
            continue

        list_targets()
        try:
            choice = int(input("請輸入要刪除的編號："))
            if 1 <= choice <= len(config["targets"]):
                removed = config["targets"].pop(choice - 1)
                save_config()
                print(f"✅ 已成功刪除 {removed['twitch_username']}！")
            else:
                print("❌ 錯誤：無效的編號！")
        except ValueError:
            print("❌ 錯誤：請輸入數字編號！")

    elif action == "exit":
        print("👋 已退出管理工具。")
        break

    else:
        print("❌ 錯誤：請輸入 'add'、'delete' 或 'exit'！")
