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

if [ "$STATUS" -ne 0 ]; then
  echo ""
  echo "未完成，请根据上面的错误提示修改。"
  read -r -p "按回车关闭…" _
  exit 1
fi

# --- 自动上传到 GitHub ---
COMMIT_DATE="${DATE:-$(date +%Y-%m-%d)}"
echo ""
echo "正在自动上传到 GitHub…"

git add -A
if git diff --cached --quiet; then
  echo "没有需要上传的改动。"
  read -r -p "按回车关闭…" _
  exit 0
fi

git commit -m "更新 $COMMIT_DATE meme" >/dev/null 2>&1

if git push origin HEAD; then
  echo ""
  echo "上传成功 ✓  约 1~2 分钟后网站会自动更新。"
  echo "网址: https://stillsayinggoodmorning.com"
else
  echo ""
  echo "！上传(push)失败。常见原因是第一次需要登录 GitHub。"
  echo "  解决办法（只需一次）："
  echo "  打开 GitHub Desktop，点一次 Push origin 完成登录，"
  echo "  之后再用这个脚本就能全自动上传了。"
  echo "  （你的改动已经 commit 保存，不会丢失。）"
fi

echo ""
read -r -p "按回车关闭…" _
