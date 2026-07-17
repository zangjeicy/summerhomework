---
name: blog
description: Write, revise, review, and optimize RuyiBookCourse blog posts in Zhang Dapeng's first-person expert voice. Use this skill when the user asks to create a blog article, polish an existing post, improve title/structure/style, write technical/project-practice posts, compare tools for a blog, or publish Markdown under the repository's 博客 directory.
---

# Blog

## Scope

Use this skill for RuyiBookCourse blog writing and editing tasks.

The goal is to produce useful Chinese project-practice articles, not generic encyclopedia entries. Treat each post as Zhang Dapeng sharing his own real development experience while building RuyiBookCourse.

## Default Workflow

1. Work from `D:\notes\RuyiBookCourse`.
2. Read nearby existing posts before writing when style matters.
3. If the topic depends on current products, tools, licenses, models, releases, or public facts, browse the web first and cite the sources inside the article or final note.
4. Choose a clear, clickable Chinese title. Prefer practical tension, contrast, or decision value over vague slogans.
5. Write the post as Markdown under `博客\YYYY年\MM月`.
6. Name files as `NNN_标题.md`, where `NNN` continues the existing numeric sequence in that month.
7. Keep the H1 exactly aligned with the title.
8. Use the opening line: `OK，OK，大家好，欢迎大家来到大鹏 AI 教育，我是张大鹏。`
9. Write from Zhang Dapeng's first-person perspective. The article should feel like his expert field note from a real project, not an anonymous AI article.
10. Ground the article in RuyiBookCourse or the user's actual workflow whenever possible.
11. After writing, read back the file path, size, and first section enough to confirm the file exists and is not empty.
12. When a blog batch or skill improvement is complete, remind that it should be committed with a detailed Chinese Git message unless the user asks not to commit.

## Writing Style

- Write in simplified Chinese.
- Use a direct first-person teaching voice: `我在这个项目里...`, `我的判断是...`, `我这次没有...`, `我准备先...`.
- Make the fixed opening serve identity and authorship: readers should know this is Zhang Dapeng sharing his real development process.
- Explain tradeoffs through concrete scenarios, commands, files, and project decisions.
- Avoid hollow marketing language, exaggerated certainty, and pure listicle filler.
- Do not expose secrets, API keys, private account details, QR codes, payment links, or conversion channels.
- Mention uncertainty when a claim is source-dependent or may change.
- For tool comparisons, avoid declaring a universal winner. State which product is better for which scenario.

### 排版铁律（手机优先，强制；详见 `references/style-guide.md`）

读者大多在手机上看，排版目标是干净、清爽、不疲惫。范本：`图书/.../博客/01_课程介绍.md`。

- **每个标题上面空四行**（H1 在文件顶部除外），让每节有明显呼吸感。
- **禁止大段落**：一段只说一件事，控制在一到两行；长句在自然停顿处断开，一行一句。
- **多用列表**：能列举的（数据/步骤/理由/提醒/清单）一律拆成列表，不写成长段。
- **每个 list item 开头配一个贴合内容的 emoji**（📊 数据 / 🤖 AI / 🔧 后端 / 🎨 前端 / 🔗 全栈 / ⚠️ 提醒 …按语义选）。
- **只用无序列表 `-`**：**禁止有序列表 `1. 2. 3.`**；必须强调先后顺序时改用「**第一**，…」「**第二**，…」「**第三**，…」。
- **禁止使用表格**：任何对比都用分点列表表达，不写 Markdown 表格。
- **金句用 `>` 引用块**单独成段、按句断行，比加粗更醒目。
- **禁止破折号 `——`**：承接/补充改用 `：`、`，` 或直接断行断句。
- **表示"逐个"用口语「挨个儿」**，不用书面的「一一」。
- **一篇最多配 3 张插图**：宁缺毋滥，图为内容服务；封面不单独做，从这 3 张插图里自选。

## Article Shape

Start with the real problem or decision.

Then build the article in this order unless the user requests another structure:

1. Why this topic matters now.
2. What the concept/tool/project actually is.
3. What problem it solves.
4. How it relates to RuyiBookCourse or local learning/course production.
5. What I would do first in this project.
6. Risks, limitations, or things not to do yet.
7. A clear next step.

For comparison articles, express the comparison as grouped bullet lists (each side a short emoji list), never as a Markdown table.

## Source Discipline

Browse before writing when the post mentions current products such as RAGFlow, FastGPT, SiliconFlow, OpenAI, model names, licenses, releases, pricing, or installation details.

Prefer official docs, GitHub repositories, release pages, license files, and primary vendor documentation. Use secondary sources only for context.

Do not paste long quotes. Summarize in your own words and link sources.

## RuyiBookCourse Defaults

Use these repository facts unless local files prove they changed:

- Project root: `D:\notes\RuyiBookCourse`
- Dependency manager: `uv`
- Parser code: `src\parse`
- Product code: `src\bookcourse`
- Raw ebooks: `source\pdf` and `source\epub`
- Generated learning material: subject/book/version directories such as `数据分析\学习 D3.js\英文版`
- Blog directory: `博客\YYYY年\MM月`
- `.env` may contain local API keys and must never be copied into posts.
- Completed blog and skill changes should be committed promptly with detailed Chinese commit messages.

Read `references\style-guide.md` when the user asks for style optimization, title optimization, or a new long-form post.
