#!/bin/bash
# Double-click: add today's meme from photos/inbox/ into the archive.
cd "$(dirname "$0")" || exit 1

echo "=============================================="
echo "  Still Saying Good Morning — 添加今日 meme"
echo "=============================================="
echo ""
echo "请先把图片放进 photos/ 或 photos/inbox/"
echo "（一次只放一张待处理的图）"
echo ""
echo "这张 meme 是「哪一天」的？"
echo "  · 直接回车 = 今天 ($(date +%Y-%m-%d))"
echo "  · 或输入日期，如 2026-06-07"
read -r -p "日期: " DATE
echo ""
read -r -p "发送时间 (24小时制, 如 10:16): " TIME

if [ -z "$TIME" ]; then
  echo "未输入时间，已取消。"
  read -r -p "按回车关闭…" _
  exit 1
fi

if [ -z "$DATE" ]; then
  python3 scripts/add_meme.py --time "$TIME"
else
  python3 scripts/add_meme.py --time "$TIME" --date "$DATE"
fi
STATUS=$?

echo ""
if [ "$STATUS" -eq 0 ]; then
  echo "然后去 GitHub Desktop → Commit → Push"
else
  echo "未完成，请根据上面的错误提示修改。"
fi
echo ""
read -r -p "按回车关闭…" _
