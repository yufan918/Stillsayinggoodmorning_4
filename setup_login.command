#!/bin/bash
# 一次性设置：把 GitHub 令牌（Token）存进 macOS 钥匙串。
# 设置成功后，add_meme.command 就能自动上传，不再询问登录。
cd "$(dirname "$0")" || exit 1

GH_USER="yufan918"

echo "=================================================="
echo "  一次性登录设置 — Still Saying Good Morning"
echo "=================================================="
echo ""
echo "这一步只需要做一次。做完之后，以后用 add_meme.command"
echo "上传就会自动完成，不会再问你 GitHub 登录。"
echo ""
echo "第 1 步：先去 GitHub 创建一个令牌（Token）"
echo "  1) 打开这个网址（复制到浏览器）："
echo "     https://github.com/settings/tokens/new"
echo "  2) Note 里随便写个名字，比如 mac terminal"
echo "  3) Expiration 选 No expiration（永不过期）"
echo "  4) 勾选 repo 这一整项"
echo "  5) 拉到最下面点 Generate token，复制生成的一串"
echo "     （以 ghp_ 开头的那串）"
echo ""
echo "第 2 步：把复制到的令牌粘贴到下面（粘贴时看不到字符，正常）"
read -r -s -p "粘贴令牌后按回车: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
  echo ""
  echo "没有输入令牌，已取消。"
  read -r -p "按回车关闭…" _
  exit 1
fi

# 存进钥匙串
printf "protocol=https\nhost=github.com\nusername=%s\npassword=%s\n" "$GH_USER" "$TOKEN" \
  | git credential-osxkeychain store

echo ""
echo "正在验证登录是否成功…"
if git ls-remote https://github.com/${GH_USER}/Stillsayinggoodmorning_4.git >/dev/null 2>&1; then
  echo "✓ 登录信息已保存。"
  echo ""
  echo "如果本地还有没上传的改动，现在帮你推送一次做最终确认…"
  if [ -n "$(git log origin/main..HEAD --oneline 2>/dev/null)" ]; then
    if git -c credential.helper=osxkeychain push origin HEAD >/dev/null 2>&1; then
      echo "✓ 推送成功，登录彻底设置完成！"
    else
      echo "！自动推送没成功，但登录信息已保存。下次用 add_meme.command 会自动上传。"
    fi
  else
    echo "（当前没有待上传的改动，一切就绪。）"
  fi
  echo ""
  echo "全部完成！以后直接用 add_meme.command，会自动上传。"
else
  echo "！验证没通过。可能令牌复制不完整，或没勾选 repo 权限。"
  echo "  可以重新跑一次这个脚本，重新创建并粘贴令牌。"
fi

echo ""
read -r -p "按回车关闭…" _
