import os
import json
import time
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 載入 .env_bot
load_dotenv(dotenv_path=".env_bot")
TOKEN = os.getenv("DISCORD_TOKEN")
print("🧪 DEBUG TOKEN:", repr(TOKEN))
if not TOKEN:
    print("❌ DISCORD_TOKEN 未正確載入，請檢查 .env_bot 檔案")
    exit(1)

# 初始化 bot
INTENTS = discord.Intents.default()
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

STATE_PATH = "live_state.json"

def load_live_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def format_duration(seconds):
    delta = timedelta(seconds=int(seconds))
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} 小時 {minutes} 分鐘"

@BOT.event
async def on_ready():
    await BOT.sync_commands()  # 確保 slash 指令註冊成功
    print(f"✅ 已登入 Discord Bot：{BOT.user.name}，Slash 指令已同步")

@BOT.slash_command(name="whoislive", description="查詢目前正在開台的實況主")
async def whoislive(ctx: discord.ApplicationContext):
    await ctx.defer()
    state = load_live_state()
    if not state:
        await ctx.respond("🔍 目前沒有任何人正在直播")
        return

    reply = "🎥 目前正在直播的實況主：\n\n"
    for idx, (streamer, info) in enumerate(state.items(), start=1):
        start_time = info.get("start_time")
        if start_time:
            start_time_dt = datetime.fromtimestamp(start_time)
            duration = format_duration(time.time() - start_time)
            start_fmt = start_time_dt.strftime("%Y-%m-%d %H:%M")
        else:
            start_fmt = "未知"
            duration = "未知"

        reply += f"{idx}. {info['nickname']}（{streamer}）\n"
        reply += f"開播時間：{start_fmt}\n"
        reply += f"已經持續實況了：{duration}\n"
        reply += f"Game: {info.get('last_game', 'Unknown')}\n"
        reply += f"Title: {info.get('last_title', '無標題')}\n"
        reply += f"Viewers: ?\n\n"

    await ctx.respond(reply.strip())

@BOT.slash_command(name="reload", description="重新載入 Twitch 設定與 webhook")
async def reload_cmd(ctx: discord.ApplicationContext):
    await ctx.defer()
    try:
        res = requests.post("http://localhost:5000/reload")
        if res.status_code == 200:
            await ctx.respond("🔁 已成功觸發主程式重新載入 webhook 與設定")
        else:
            await ctx.respond(f"⚠️ 主程式返回狀態碼：{res.status_code}")
    except Exception as e:
        await ctx.respond(f"❌ 無法連接主程式：{e}")

if __name__ == "__main__":
    BOT.run(TOKEN)
