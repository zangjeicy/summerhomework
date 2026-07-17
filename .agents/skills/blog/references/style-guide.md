# RuyiBookCourse Blog Style Guide

## Positioning

RuyiBookCourse blogs are Zhang Dapeng's first-person project-practice notes for turning ebooks into courses with AI. They should help the reader understand a real technical or product decision, while preserving the working rhythm of the project.

The article should not sound like a neutral encyclopedia or generic AI summary. It should sound like Zhang Dapeng reviewing what he actually did, why he did it, what he avoided, and what he will improve next.

## Fixed Opening

Use this exact opening after the H1:

`OK，OK，大家好，欢迎大家来到大鹏 AI 教育，我是张大鹏。`

This line is not decoration. It establishes authorship. After it, continue in the same first-person voice instead of switching into anonymous third-person explanation.

## Good Titles

Prefer titles that contain a concrete object and a decision or tension:

- `RAGFlow到底强在哪？别只把它当知识库`
- `FastGPT爆火的原因：它不是普通知识库`
- `RAGFlow和FastGPT怎么选？选错会很痛`
- `RuyiBookCourse项目如何通过硅基流动接入RAG知识库`
- `我在RuyiBookCourse里创建本地技能：让AI真正学会我的项目方法`

Avoid empty titles such as:

- `关于RAG的思考`
- `知识库平台介绍`
- `项目总结`

## 排版规范（手机优先，强制）

读者大多在手机上看。排版的唯一目标是：**干净、清爽、不疲惫**。以下为硬性规则，案例范本见 `博客/.../01_课程介绍.md`。

### 1. 每个标题上面留四个空行

每个 `##` / `###` 标题之前，**空四行**（H1 在文件最顶部除外）。让每一节之间有明显的呼吸感，滑动时一眼能看到段落分界。

### 2. 禁止大段落，长句拆成多行

- 不允许一坨密密麻麻的长段落。
- 一个自然段通常只说一件事，控制在一到两行。
- 一句话太长，就在自然停顿处断开，**一行一句**，每行短一点，手机上不用左右找。

```markdown
AI 给你的，是一个"看起来对"的答案。

至于它到底对不对，得有一个看得懂的人来把关。
```

### 3. 多用列表（**只用无序列表**）

凡是能列举的内容（数据、步骤、理由、对比、提醒、清单），一律拆成列表，不要写成一长段。

**只用 `-` 无序列表，禁止 `1. 2. 3.` 有序列表。** 列表的顺序感由「第一 / 第二 / 第三」这类口语词承担，比阿拉伯数字更亲切，也避免在手机上跟其他标号视觉打架。

如果真的有强先后顺序：

- ✅ **第一**，先把环境搭好
- ✅ **第二**，再学后端
- ✅ **第三**，最后打通前后端
- ❌ `1. 先把环境搭好`（禁止）

### 4. 列表每一项配一个贴合内容的 emoji

每个 list item 开头放**一个**和该项内容匹配的 emoji，作视觉锚点。要贴合语义，不是随便撒。

```markdown
- 📈 **84% 的开发者**已经在用 AI 工具
- 🐍 后端用 Python + Django
- 🎨 前端用 Vue
- ⚠️ 别全信 AI，它写的每一段你都要能判断对不对
```

常用对照（按语义选，不必拘泥）：📊📈 数据 / 🤖 AI / 🔧 后端 / 🎨 前端 / 🔗 打通·全栈 / 🛠️⚙️ 环境·工具 / ⚠️🚫 提醒·风险 / ✅ 正确做法 / 🐛🔌🔓 各类坑 / 🚀⚡ 性能 / 📅⏳ 时间·进度。

有序步骤用 `1. 2. 3.`，同样每项配 emoji。

### 5. 禁止使用表格

任何情况下**不用 Markdown 表格**。要做对比，用「分点列表 / 小标题 + 列表」表达，别用 `| --- |`。表格在手机上会挤成一团。

### 6. 金句用引用块独立出来

最想让读者记住的那一两句，用 `>` 引用块单独成行、单独成段，并按句断行。这样它从正文里"跳"出来，比加粗更醒目。

```markdown
> 真正的问题不是 AI 会不会写代码，
> 而是 AI 写出来的代码，谁来负责。
```

### 7. 禁止破折号 `——`

正文**一律不用破折号 `——`**。需要承接、补充、解释时，改用更轻的标点或直接断行：

- ✅ `：` 引出说明（`先把环境搭好：装好 Python、Node.js`）
- ✅ `，` 顺接下半句（`判断对不对，这正是你学这门课的目的`）
- ✅ 直接断成新的一句 / 新的一行，留白本身就是停顿

```markdown
又不会掉进那些不敢信 AI 的人担心的坑里。

因为你看得懂。
```

### 8. 表示"逐个"用口语「挨个儿」

要表达「一一 / 逐个」的意思，用更口语的 **「挨个儿」**，别用书面的「一一」，更贴张大鹏的说话口吻。

- ✅ 我们挨个儿把它讲清楚
- ❌ 我们一一把它讲清楚

避免：不加任何拆分的学术式长段（除非用户明确要正式报告）。

## First-Person Expert Voice

Use `我` when describing decisions, tradeoffs, and next steps.

Good:

```markdown
我这次没有把它做成全局技能。

因为这个博客规范不是所有项目都适用，它属于 RuyiBookCourse。
```

Avoid:

```markdown
本文将介绍如何创建技能。

用户可以根据需要选择全局或项目级配置。
```

## Technical Detail

Concrete details make the blog useful. Include paths, commands, and project decisions when relevant:

```powershell
uv run bookcourse rag index
uv run bookcourse rag query "Python 数据分析这本书应该怎么学？"
```

Do not turn the post into raw documentation. Explain why the command or design matters.

## Comparison Posts

Use this pattern:

1. Give the one-sentence difference.
2. Explain each side's real positioning.
3. Map each option to scenarios.
4. State what RuyiBookCourse should do first.
5. Name risks and license/deployment concerns.

## Public Safety

Keep posts suitable for public publishing:

- Do not include real API keys.
- Do not include private service entry points.
- Do not include payment, QR, account, or conversion copy.
- Do not claim private revenue, private customer data, or unverified internal facts.

## Ending

End with a practical next action. The article should leave the reader knowing what to do, not just what to think.

## Commit Habit

After finishing a blog batch or blog-skill improvement, preserve the recovery point with Git. Use a detailed Chinese commit message that names the blog batch, the skill/rule change, and the reason for the change.
