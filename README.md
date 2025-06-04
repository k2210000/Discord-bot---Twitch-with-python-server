# Twitch 推播 Discord 機器人

一個自動查詢 Twitch 實況主開台與關台狀態，並將狀態即時推送至 Discord 頻道的輕量級 BOT
支援自動觀眾數更新、遊戲分類變更、縮圖顯示、使用者標記等功能

讓你不再錯過自己喜歡的實況主或是你推！

---

## 功能特色

![Image](https://github.com/user-attachments/assets/d276bb48-663b-47dc-8135-eda6d25d4e5f)

- ✅ 自動查詢多位 Twitch 實況主的開台與關台
- 📢 自動將開台訊息推送至 Discord webhook 頻道
- 🔁 持續更新觀眾數、遊戲分類與標題（每分鐘抓取一次）
- 🎯 支援 @mention 指定 Discord 使用者
- 🔐 支援 Twitch EventSub Webhook 機制
- 🌐 使用 ngrok 暴露本地端伺服器供 Twitch webhook callback

---

## 安裝方式

1.至release下載壓縮檔並找到你要安裝的地方解壓縮

2.安裝 Python 套件（建議 Python 3.9+）：

```pip install -r requirements.txt```

3.前往 ngrok 註冊帳號，並設定好 ngrok authtoken

4.建立 config.json 設定檔，範例如下：

```
{
  "twitch": {
    "client_id": "你的_Twitch_Client_ID",
    "client_secret": "你的_Twitch_Client_Secret"
  },
  "mention_user_id": "你的Disocrd id",
  "targets": [
    {
      "twitch_username": "實況主帳號",
      "nickname": "",
      "discord_webhook": "https://discord.com/api/webhooks/xxx/yyy"
    }
  ]
}
```
```Twitch_Client_ID```和```Twitch_Client_Secret```可以至[Twitch dev](https://dev.twitch.tv/console/apps)取得

建立時重新導向網址請輸入```http://localhost:5000```並在分類選擇```Application Integration```

mention的ID可點擊discord左下角頭像 →「複製使用者 ID」

想要查詢的實況主可以使用```manage_targets.py```來進行增加

![Image](https://github.com/user-attachments/assets/bcac97ff-0719-4acc-860f-b88fc3879ad6)

```Discord webhook```將在此詢問要不要輸入，第一次使用請務必輸入，第二位之後直接按Enter將以預設webhook執行新增，如果需更換可以再輸入其他webhook

5.在 ```.env_bot``` 設定檔中設置discord token (如不使用/slash指令可跳過)

首先你需要取得一個discord bot token

至[Discord developers](https://discord.com/developers/applications)建立一個Bot，命名為喜歡的名稱

建立應用程式後，至Installation底下給予```Send Messages```、```Read Message History```和```Use Application Commands```權限，或是直接給予```Administrator```管理員權限

往上滑到```Install Link```獲取連結邀請進入伺服器

左邊選取```Bot```欄位，至```Token```處取得Discord Token並輸入至```.env_bot```中

6.執行```Run.bat```將會開啟```除錯用bot視窗```、```本體```、```ngrok伺服器```

---

## 結尾
歡迎 Issue、PR、與 Star！

如有問題請開啟 GitHub Issues 或聯絡作者 

Discord ID: phantom0629

---

## 授權 License
本專案採用 BSD 3-Clause License，可自由修改與使用，請保留原始作者資訊。
