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
  # 添加这一步失败了。但如果只是「这天已经加过」，本地可能还有【尚未上传到
  # 网站】的改动，这种情况仍然让你去上传，不算真正失败。
  if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "提示：这张图可能之前已经加过了，但检测到本地还有【尚未上传到网站】的改动。"
    echo "      可以继续把这些改动上传到网站。"
  else
    echo ""
    echo "未完成，请根据上面的错误提示修改。"
    read -r -p "按回车关闭…" _
    exit 1
  fi
fi

# --- 确认后上传到网站（GitHub） ---
COMMIT_DATE="${DATE:-$(date +%Y-%m-%d)}"

if [ -z "$(git status --porcelain)" ]; then
  echo ""
  echo "没有需要上传的改动。"
  read -r -p "按回车关闭…" _
  exit 0
fi

echo ""
echo "----------------------------------------------"
echo "本次将上传到网站的改动："
git status --short
echo "----------------------------------------------"
echo ""
echo "确认现在上传到网站吗？"
echo "  · 回车 或 y = 确认上传"
echo "  · n = 先不上传（改动会保留在本地，下次可再传）"
read -r -p "请选择: " CONFIRM

case "$CONFIRM" in
  n|N|no|NO|否)
    echo ""
    echo "已取消上传。你的改动已保存在本地，随时可再运行本脚本上传。"
    read -r -p "按回车关闭…" _
    exit 0
    ;;
esac

echo ""
echo "正在上传到网站…"
git add -A
git commit -m "更新 $COMMIT_DATE meme" >/dev/null 2>&1

# 用 macOS 钥匙串里的 GitHub 凭据推送（GitHub Desktop 登录过就能直接用），
# 不修改任何全局 git 配置。
if git -c credential.helper=osxkeychain push origin HEAD; then
  echo ""
  echo "上传成功 ✓  约 1~2 分钟后网站会自动更新。"
  echo "网址: https://stillsayinggoodmorning.com"
else
  echo ""
  echo "！上传(push)失败。常见原因是这台电脑还没登录过 GitHub。"
  echo "  解决办法（只需一次）："
  echo "  打开 GitHub Desktop，点一次 Push origin 完成登录，"
  echo "  之后再用这个脚本就能全自动上传了。"
  echo "  （你的改动已经 commit 保存，不会丢失。）"
fi

echo ""
read -r -p "按回车关闭…" _
