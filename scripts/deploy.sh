#!/usr/bin/env bash
# SnowmanBlog 一键部署脚本
# 用法: ./scripts/deploy.sh
# 前提: 本机已配置到服务器的 SSH 免密登录
set -euo pipefail

SERVER="root@120.76.142.249"
REMOTE_DIR="/www/wwwroot/pysnwomanblog"
TARBALL="/tmp/snowblog_deploy.tar.gz"

cd "$(dirname "$0")/.."

echo ">> [1/5] 打包(git archive,仅含已提交文件)"
git archive -o "$TARBALL" HEAD

echo ">> [2/5] 上传"
scp -q -o BatchMode=yes "$TARBALL" "$SERVER:$TARBALL"

echo ">> [3/5] 解压 + collectstatic + migrate"
ssh -o BatchMode=yes "$SERVER" "
  cd $REMOTE_DIR &&
  tar xzf $TARBALL &&
  source .env.deploy &&
  export PYTHONPATH=$REMOTE_DIR &&
  .venv/bin/python manage.py migrate --noinput &&
  .venv/bin/python manage.py collectstatic --noinput >/dev/null &&
  echo '   migrate + collectstatic OK'
"

echo ">> [4/5] 重启服务(systemd)"
ssh -o BatchMode=yes "$SERVER" "systemctl restart snowblog-gunicorn snowblog-celery-worker snowblog-celery-beat"

echo ">> [5/5] 健康检查"
sleep 3
code=$(ssh -o BatchMode=yes "$SERVER" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/")
if [ "$code" = "200" ]; then
  echo "✅ 部署成功(http://pyblog.snowmannunu.top)"
else
  echo "❌ 健康检查失败(HTTP $code),请查看: journalctl -u snowblog-gunicorn -n 20"
  exit 1
fi
