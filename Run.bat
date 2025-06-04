@echo off
cd /d %~dp0

echo 啟動 Twitch 主程式...
start "" python "%~dp0twitch_discord_notify.py"
timeout /t 3

echo 啟動 Discord Bot...
start "" python "%~dp0push.py"