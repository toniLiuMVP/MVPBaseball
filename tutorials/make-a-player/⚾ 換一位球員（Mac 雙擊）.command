#!/bin/bash
# TOOL_DATE = '2026-09-23'
# 雙擊這個就好。它會開一個視窗,一句一句問你。
cd "$(dirname "$0")"
clear
# 不能只看「python3 這個名字在不在」:本站測試機的 /usr/bin/python3 是系統內建的
# 轉接檔(跟 /usr/bin/git 是同一個檔),沒裝開發者工具的 Mac 上它會跳出安裝視窗,
# 而不是真的跑 Python(這一點本站還沒在沒裝開發者工具的 Mac 上實測)。
# 所以真的跑一次,而且要 3.7 以上(換球員工具用到的功能 3.7 才有)才算有。
PY=""
for c in python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if "$c" -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
if [ -n "$PY" ]; then
  "$PY" mvp_player.py
else
  echo
  echo "  這台電腦還沒有能用的 Python(要 3.7 以上)。"
  echo "  剛剛如果跳出要你安裝「開發者工具」的視窗,按「安裝」,裝完再雙擊一次。"
  echo "  沒有跳出視窗的話,到 https://www.python.org/downloads/ 下載 macOS 版,裝完再雙擊一次。"
  echo
fi
echo
read -n 1 -s -r -p "  按任意鍵關閉這個視窗。"
echo
