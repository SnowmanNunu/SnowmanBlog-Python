#!/usr/bin/env bash
# 一键推送到 GitHub 与 Gitee 双远程
# 用法: ./scripts/push-all.sh [分支名(默认当前分支)] [--tags]
set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="${1:-$(git branch --show-current)}"
EXTRA="${2:-}"

echo ">> 推送分支: $BRANCH"
for remote in origin gitee; do
  echo ">> pushing -> $remote ($BRANCH)"
  git push "$remote" "$BRANCH" $EXTRA
done

echo "✅ 双远程推送完成 (origin=GitHub, gitee=Gitee)"