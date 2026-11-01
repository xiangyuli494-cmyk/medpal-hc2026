#!/usr/bin/env bash
# 一次性把本地护栏装好：主干改名 main + 启用 .githooks + 关掉 push 到 main 的可能
#
#   bash tools/setup-git.sh            # 只装护栏
#   bash tools/setup-git.sh --commit   # 装护栏 + 建仓第一个提交（在 main 上）
#
# Windows 上用 Git Bash / WSL 跑；PowerShell 里用 bash tools/setup-git.sh。

set -e
cd "$(dirname "$0")/.."

echo "→ 仓库：$(pwd)"

# 1 主干统一叫 main
if [ -d .git ]; then
  current="$(git symbolic-ref --short HEAD 2>/dev/null || echo '')"
  if [ "$current" != "main" ]; then
    git symbolic-ref HEAD refs/heads/main
    echo "→ 主干已改名为 main（原：${current:-未出生}）"
  else
    echo "→ 主干已是 main"
  fi
else
  git init -q
  git symbolic-ref HEAD refs/heads/main
  echo "→ 已 git init，主干为 main"
fi

# 2 启用仓库内钩子
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push 2>/dev/null || true
echo "→ core.hooksPath = .githooks（pre-commit / pre-push 已生效）"

# 3 提交时统一换行，避免 Windows 上整文件 diff
git config core.autocrlf false
echo "→ core.autocrlf = false"

# 4 首个提交（可选）
if [ "$1" = "--commit" ]; then
  if git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "→ 已有提交，跳过首个提交"
  else
    git add -A
    ALLOW_MAIN=1 git commit -q -m "chore: 初始化仓库骨架（比赛规划 + 设计文档 + 协作规则）"
    echo "→ 已在 main 上建立首个提交"
    git --no-pager log --oneline -1
  fi
fi

echo ""
echo "完成。现在的规矩："
echo "  · main 只读，在 main 上 commit / push 都会被拦"
echo "  · 开分支：git switch -c t2/视觉系统-1104"
echo "  · 合并前要 2 个 Approve（T1 + 线负责人），服务器端在 GitHub Settings → Branches 里配"
echo "  · 详见 CONTRIBUTING.md"
