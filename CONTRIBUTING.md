# 协作与分支规则

> **`main` 只读。任何改动都在分支上，开 PR，等 Approve 才合并。**
> 这条不是形式主义：4 个人改同一份 Figma 导出目录和同一批 md，没有 PR 就有三种"最终版"。

---

## 1 前提：本地护栏已装好

> **克隆仓库之后的第一件事**：跑一次 `bash tools/setup-git.sh`。
> 钩子不进版本库（`core.hooksPath` 是本地配置），不跑这一步，你的机器上就拦不住 `main`。

```bash
bash tools/setup-git.sh                 # 装护栏（推荐，一次就够）
git config core.hooksPath .githooks     # 效果同上，手动版
```

装好之后：

- 在 `main` 上 `git commit` → **被拦**
- 往 `main` `git push` → **被拦**

唯一的绕过方式（只在建仓/救火时用）：

```bash
ALLOW_MAIN=1 git commit -m "chore: 初始化骨架"
```

---

## 2 分支命名

```
<编号>/<做什么>-<月日>
```

| 例子 | 谁的 | 做什么 |
| --- | --- | --- |
| `t1/信息架构-1106` | T1 | 信息架构定稿 |
| `t2/视觉系统-1104` | T2 | 视觉系统页冻结 |
| `t2/七屏导出-1116` | T2 | 导出 9 张 2x |
| `t3/流程图-1117` | T3 | 主流程图 |
| `t4/原话卡-1107` | T4 | 访谈原话卡 |

规矩：**一个人同时只开一条分支**；一条分支只服务一个交付物；做完合掉再开下一条。

---

## 3 五步流程（贴墙上）

```bash
# 1 先同步
git switch main && git pull

# 2 开分支
git switch -c t2/视觉系统-1104

# 3 干活 + 小步提交
git add 02-design/04-视觉系统.md
git commit -m "feat(T2): 视觉系统页冻结-色板与字阶"

# 4 推分支（只推自己的分支）
git push -u origin t2/视觉系统-1104

# 5 去 GitHub 点 "Compare & pull request" → 填模板 → 等 Approve → Squash and merge → 删分支
```

---

## 4 谁批谁（CODEOWNERS 会自动 @ 人）

| 改了什么 | 必须 Approve |
| --- | --- |
| `02-design/04-视觉系统.md`、`04-deliverables/01-高保真图/`、`04-deliverables/04-展板/` | **T2** |
| `02-design/02-信息架构.md`、`03-交互流程.md`、`01-competition/` | **T1** |
| `04-deliverables/02-流程图/`、`03-视频/` | **T3** |
| `05-research/`、`04-deliverables/05-设计说明/`、全部界面文案 | **T4** |
| **任何分支要进 `main`** | **T1 必点 + 该线负责人再点**（共 2 个 Approve） |

> 2 个 Approve 的作用：防止自己批自己。4 人团队里这是唯一有效的一道闸。

---

## 5 commit message 规矩

```
<类型>(<编号>): <做了什么>
```

| 类型 | 用在哪 |
| --- | --- |
| `feat` | 新增交付内容（一屏、一章、一张流程） |
| `fix` | 修正（错字、错色、溢出） |
| `docs` | 只改 md |
| `asset` | 只加/换二进制（PNG、MP4、PDF） |
| `chore` | 目录、脚本、配置 |

- 一次提交只做一件事
- 禁止 `update`、`111`、`最终版`、`final`、`asdf`
- 中文写清楚做什么，写不清说明这次提交掺了太多东西

---

## 6 PR 规矩

1. 标题与 commit 同格式
2. 正文用 `.github/pull_request_template.md`，勾选对应门禁 G1–G5
3. 一个 PR **≤ 20 个文件**；超了拆开
4. 二进制资产（PNG / MP4 / PDF）单独一个 PR，打 `asset` 标签
5. 视觉类 PR **必须贴截图**——评委看不到分支，但组员要能一眼判断对不对
6. PR 合并后立刻删分支，别留一堆 `t2-2`、`t2-最终`

---

## 7 冲突处理

- 谁的分支谁负责：`git pull --rebase origin main`
- 任何分支都不许 `push -f`
- 同一文件两人同时改 → **后提交的人负责 rebase**，并在群里 @ 前一个人
- 二进制文件（.fig / .psd / .mp4）冲突无法合并 → **约定同一时间只有一个人动**，改之前在群里喊一句

---

## 8 服务器端设置（一次性，T1 在 GitHub 上做）

仓库建好后 → **Settings → Branches → Add branch protection rule**

- Branch name pattern：`main`
- ☑ Require a pull request before merging
  - Required approvals：**2**
  - ☑ Dismiss stale pull request approvals when new commits are pushed
- ☑ Require review from Code Owners
- ☑ Do not allow bypassing the above settings（管理员也不许）
- ☑ Require conversation resolution before merging
- 不勾 Require status checks（我们没跑 CI）

命令行版（装了 `gh` 且已登录时一行搞定）：

```bash
gh api --method PUT repos/OWNER/REPO/branches/main/protection \
  -F required_status_checks=null \
  -F enforce_admins=true \
  -F required_pull_request_reviews[required_approving_review_count]=2 \
  -F required_pull_request_reviews[dismiss_stale_reviews]=true \
  -F required_pull_request_reviews[require_code_owner_reviews]=true \
  -F restrictions=null
```

> ⚠️ 分支保护只对**远程**生效。本地靠 `.githooks/` 那两个脚本拦，两者都要有。

---

## 9 CODEOWNERS 要改一处

`.github/CODEOWNERS` 里的 `@T1-handle` 是占位符，**换成四个人的真实 GitHub 用户名**，否则不会自动 @ 人、也不会自动要求审批。

---

## 10 例外与红线

| 情况 | 怎么办 |
| --- | --- |
| 建仓第一次提交 | 允许直接在 `main`：`ALLOW_MAIN=1 git commit` |
| 第一次把主干推到远程 | 允许一次：`ALLOW_MAIN=1 git push -u origin main`（之后 `main` 只从 PR 进） |
| 11-25 上传当天发现致命错误 | 仍走分支 + PR，但**只批 1 人**（T1 单点放行），事后在 PR 里补一句原因 |
| 有人直接改了 `main` | 当天必须补一个 PR 把改动"追认"回来，写明发生了什么 |
| 为了赶时间跳过 PR | 不许。跳过一次，后面就没有"哪版是准的" |

---

## 11 一页速查

```text
主干 main：只读
分支：<编号>/<做什么>-<月日>
提交：feat(T2): 视觉系统页冻结
推送：只推自己的分支
合并：2 个 Approve（T1 + 线负责人），Squash and merge
被杀：在 main 上 commit / push 会被本地钩子拦
```
