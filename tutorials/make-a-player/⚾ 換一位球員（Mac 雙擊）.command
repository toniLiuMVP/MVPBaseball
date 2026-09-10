#!/bin/bash
# 雙擊這個就好。它會開一個視窗,一句一句問你。
cd "$(dirname "$0")"
clear
if command -v python3 >/dev/null 2>&1; then
  python3 mvp_player.py
else
  echo
  echo "  這台電腦還沒有 Python。"
  echo "  到 https://www.python.org/downloads/ 下載安裝,再回來雙擊一次。"
  echo
fi
echo
read -n 1 -s -r -p "  按任意鍵關閉這個視窗。"
echo
