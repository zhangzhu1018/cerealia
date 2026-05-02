#!/bin/bash
# serveo 隧道启动脚本
# 首次使用固定子域名需：ssh-keygen -t rsa && 注册到 https://serveo.net
# 当前使用随机 URL，每次重启需要新 URL 并更新前端代码

SUB="caviar-crm"
kill $(pgrep -f "serveo.net") 2>/dev/null
sleep 1

echo "启动隧道..."
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R ${SUB}:80:localhost:5001 serveo.net 2>&1 | while read line; do
  echo "$line"
  # 提取随机 URL
  if [[ "$line" =~ https://([a-z0-9]+).serveo ]]; then
    URL="https://${BASH_REMATCH[1]}-.serveousercontent.com"
    echo "新URL: $URL"
    echo "$URL" > /tmp/caviar_serveo_url.txt
  fi
done
