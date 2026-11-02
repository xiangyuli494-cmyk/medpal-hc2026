#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""匿名自检：提交前跑一遍，别让一个用户名毁掉整份材料。

    python tools/anon_check.py

分两级：
  硬伤（退出码 1）  禁用词、真实手机号、身份证、邮箱、作品材料里的可追溯外链
  提示（不阻塞）    机构名——策划文档里引用主办与赛区高校是正常的，需要人看一遍

规矩：
  - 01-competition/ 是内部策划档，引用官方来源的链接是必要的，不做外链检查
  - 05-research/ 的访谈原话必须是脱敏写法，正常
  - 本脚本自身不检查自身

把你自己要防的词写进 BANNED 里，这是唯一需要改的地方。
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 禁用词（出现即失败）--------------------------------------------
BANNED = [
    # '你的真名',
    # '你的学校',
    # '你的 GitHub 用户名',
    'xiangyuli494',
    'github.io/medpal',
]

# ---- 硬伤模式 -------------------------------------------------------
# 每条：(正则, 说明, 适用范围)  适用范围 None = 所有文件
HARD = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "疑似真实手机号（演示请用 138****6688 形式）", None),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "疑似身份证号", None),
    (r"[\w.+-]+@[\w-]+\.(?:com|cn|net|org|edu|gov|io|co)\b", "邮箱地址", None),
    (r"https?://(?!127\.0\.0\.1|localhost)[\w.-]+\.[a-z]{2,}",
     "作品材料里的外部链接", "deliverable"),
]

# ---- 提示模式（只提醒，不失败）--------------------------------------
SOFT = [
    (r"(大学|学院|学校|附属医院|人民医院|中心医院)", "机构名：确认是否真实单位", None),
]

# .git 历史里允许出现的邮箱域：中性仓库身份不算泄漏
SAFE_EMAIL_DOMAINS = ("users.noreply.github.com", "example.com", "localhost")

TEXT_EXT = {".md", ".txt", ".html", ".css", ".js", ".json", ".py", ".svg", ".yml", ".yaml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "04-deliverables"}
SKIP_FILES = {os.path.join("tools", "anon_check.py")}

# 内部策划档：允许引用官方来源
INTERNAL_PREFIXES = ("01-competition",)


def in_scope(scope, rel):
    if scope is None:
        return True
    if scope == "deliverable":
        return not rel.replace("\\", "/").startswith(INTERNAL_PREFIXES)
    return True


def walk():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                yield os.path.join(base, name)


def git_history():
    """扫 .git 的提交作者与提交说明——文件遍历会跳过 .git，这是原来漏掉的一层。"""
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "log", "--all", "--format=%an%x1F%ae%x1F%s"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    hits, seen = [], set()
    for line in out.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 3:
            continue
        blob = "%s <%s> %s" % (parts[0], parts[1], parts[2])
        if blob in seen:
            continue
        seen.add(blob)
        for word in BANNED:
            if word and word in blob:
                hits.append((".git 提交历史", 0, "禁用词：%s" % word, blob[:80]))
        for pattern, why, scope in HARD:
            if scope is None or scope == "deliverable":
                for m in re.finditer(pattern, blob):
                    hit = m.group(0)
                    if why.startswith("邮箱") and hit.split("@")[-1].lower() in SAFE_EMAIL_DOMAINS:
                        continue
                    hits.append((".git 提交历史", 0, "%s：%s" % (why, hit), blob[:80]))
    return hits


def main():
    hard_hits, soft_hits, scanned = [], [], 0

    for path in walk():
        rel = os.path.relpath(path, ROOT)
        if rel in SKIP_FILES:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        scanned += 1

        for no, line in enumerate(lines, 1):
            for word in BANNED:
                if word and word in line:
                    hard_hits.append((rel, no, "禁用词：%s" % word, line.strip()[:80]))
            for pattern, why, scope in HARD:
                if not in_scope(scope, rel):
                    continue
                for m in re.finditer(pattern, line):
                    hard_hits.append((rel, no, "%s：%s" % (why, m.group(0)), line.strip()[:80]))
            for pattern, why, scope in SOFT:
                if not in_scope(scope, rel):
                    continue
                for m in re.finditer(pattern, line):
                    soft_hits.append((rel, no, "%s：%s" % (why, m.group(0)), line.strip()[:80]))

    gh = git_history()
    if gh is None:
        print("（不是 git 仓库或读不到历史：跳过 .git 检查）")
    else:
        hard_hits.extend(gh)

    print("扫描 %d 个文本文件%s" % (scanned, " + .git 提交历史" if gh is not None else ""))

    if soft_hits:
        print("\n提示 %d 处（引用主办与赛区高校属正常，确认一遍即可）：" % len(soft_hits))
        for rel, no, why, snippet in soft_hits[:10]:
            print("  %s:%d  %s\n      %s" % (rel, no, why, snippet))
        if len(soft_hits) > 10:
            print("  …… 其余 %d 处省略" % (len(soft_hits) - 10))

    if hard_hits:
        print("\n硬伤 %d 处，提交前必须处理：" % len(hard_hits))
        for rel, no, why, snippet in hard_hits:
            print("  %s:%d  %s\n      %s" % (rel, no, why, snippet))
        return 1

    if gh is not None:
        print("\n通过：工作区文本与 .git 提交历史都没有发现身份痕迹。")
    else:
        print("\n通过：工作区文本没有发现身份痕迹（.git 历史本次未检查）。")
    return 0


if __name__ == "__main__":
    try:
        # 以 UTF-8 输出，PowerShell 7 / Windows Terminal 直接可读
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
