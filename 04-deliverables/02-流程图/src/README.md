# 流程图源文件

这里放流程图的**源**，不是导出图。四条规矩：

1. **改图必须改源。** 导出 PDF 与源文件对不上的，按没做算。
2. **一个图一个文件**：`主流程.mmd`、`三通道.mmd`、`异常降级.mmd`。不新建第四个，也不合并。
3. **导出放上一层**：`04-deliverables/02-流程图/小暖_流程图_主流程.pdf`。
4. **评审看源文件**。PR 里 T1 逐行看的就是这些文本，不是 PDF——PDF 不能逐行批注。

## 先说清楚：GitHub 不会渲染 `.mmd`

GitHub 只渲染 **Markdown 里嵌的** ```` ```mermaid ```` 代码块。独立的 `.mmd` 文件点开是纯文本，看到的是代码，不是图。

别把"在 GitHub 上点开能看图"写进任何验收标准——做不到。想看效果只有三条路：

| 办法 | 适合谁 | 代价 |
| --- | --- | --- |
| VS Code 装 **Markdown Preview Mermaid Support** 或 **Mermaid Preview** 插件 | 日常改图的人 | 装一次 |
| 把内容贴到 <https://mermaid.live> | 只想看一眼的人，手机上也能用 | 复制粘贴 |
| `npx -y @mermaid-js/mermaid-cli -i src/主流程.mmd -o /tmp/主流程.png` | 要出图给评委 | 第一次会下 Chromium |

## 为什么还是用 `.mmd` 而不是 `.md`

`.md` 里包一层 ```` ```mermaid ```` 确实能在 GitHub 上直接看图，但：

- T3 已经在 `.mmd` 上做了 PR #4（内容 + 泳道重排），改格式等于让他返工一次；
- `mmdc` 直接吃 `.mmd`，转 `.md` 后导出还得先抽代码块，多一步；
- 评委看的是 **A3 PDF**，不是 GitHub 预览页。

所以：**`.mmd` 是内容真源，GitHub 上看到代码是正常的**。要在 PR 里看到图，把 mermaid.live 的分享链接或导出的 PNG 贴进 PR 描述即可。

## 为什么不用 Visio / draw.io / Figma 存源

| | `.mmd` | draw.io | Visio / Figma |
| --- | --- | --- | --- |
| PR 里逐行批注 | ✅ | ⚠️ XML 能读但难改 | ❌ 二进制 |
| 改一个措辞 | 改一行字 | 拖一个框 | 拖一个框 |
| 体积 | 1 KB | 几十 KB | 几百 KB–几 MB |
| 五人 clone 成本 | 无感 | 略慢 | 明显变慢 |

## 怎么导出 PDF

```bash
# 只要一张 PDF（-f 按图的实际尺寸出页，不压成小块）
npx -y @mermaid-js/mermaid-cli -i src/主流程.mmd -o 小暖_流程图_主流程.pdf -f

# 先出一张 2400px 宽的 PNG 打底，再照《06-流程图视觉规范》排版
npx -y @mermaid-js/mermaid-cli -i src/主流程.mmd -o /tmp/主流程-raw.png -w 2400
```

不想装 Node 就用 <https://mermaid.live>：粘贴 → Export → PDF。

## 现状

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `主流程.mmd` | 🟡 v0 | T1 从 `02-design/03-交互流程.md` 摘出，T3 在 PR #4 里接管 |
| `异常降级.mmd` | 🟡 v0 | 同上，6 条异常全在 |
| `三通道.mmd` | 🟡 v0 | 只是骨架，泳道细节要 T3 补 |
