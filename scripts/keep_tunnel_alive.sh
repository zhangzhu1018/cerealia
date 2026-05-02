#!/bin/bash
# 隧道自动保活脚本 — localhost.run
# 用法: bash scripts/keep_tunnel_alive.sh

echo "🚇 启动隧道保活..."
while true; do
  ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=2 \
    -R 80:localhost:5001 nokey@localhost.run 2>&1 | while read line; do
    if [[ "$line" =~ ([a-z0-9]+)\.lhr\.life ]]; then
      URL="https://${BASH_REMATCH[1]}.lhr.life"
      echo "隧道已连接: $URL"
      # 自动更新前端 .env
      echo "VITE_API_URL=$URL" > /Users/zhangzhu/WorkBuddy/20260425205635/caviar_crm_app/frontend/.env.production
    fi
  done
  echo "⚠️ 隧道断开，5秒后重连..."
  sleep 5
done
