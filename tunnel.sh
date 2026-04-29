#!/bin/bash
# Caviar CRM 后端隧道守护脚本
# 用法：./tunnel.sh start
# 停止：./tunnel.sh stop
# 状态：./tunnel.sh status

NAME="caviar-tunnel"
HOST="serveo.net"
PORT=5001
PID_FILE="/tmp/${NAME}.pid"
LOG_FILE="/tmp/${NAME}.log"
BACKEND_URL_FILE="/tmp/${NAME}.url"

start() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "隧道已在运行 PID=$(cat $PID_FILE)"
    cat "$BACKEND_URL_FILE" 2>/dev/null
    return 0
  fi
  echo "启动后端隧道 (serveo.net)..."
  nohup ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:${PORT} \
    ${HOST} > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  sleep 8
  URL=$(grep -o 'https://[^ ]*serveousercontent.com' "$LOG_FILE" | head -1)
  if [ -n "$URL" ]; then
    echo "$URL" > "$BACKEND_URL_FILE"
    echo "隧道已启动：$URL"
  else
    echo "URL 未立即捕获，查看日志：tail $LOG_FILE"
    tail -5 "$LOG_FILE"
  fi
}

stop() {
  if [ -f "$PID_FILE" ]; then
    kill "$(cat $PID_FILE)" 2>/dev/null && echo "已停止" || echo "进程已不存在"
    rm -f "$PID_FILE"
  else
    echo "隧道未运行"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "隧道运行中 PID=$(cat $PID_FILE)"
    echo "URL: $(cat $BACKEND_URL_FILE 2>/dev/null)"
  else
    echo "隧道未运行"
  fi
}

case "$1" in
  start) start ;;
  stop)  stop ;;
  status) status ;;
  *)     echo "用法: $0 {start|stop|status}" ;;
esac
