# 安装与激活

**尚未在 Grok Bot 中测试。** 本文件是人工步骤，不是安装器。

官方说明见 [Skills and routines](https://docs.x.ai/grok-bot/skills-routines-and-automations)。技能是一组可复用的指令。文档中的保存方式是：在对话里请 Bot 把一套步骤保存为具名技能；使用时按名称提出请求。Connect apps 用于发现和安装已支持的应用与打包技能。本仓库不是打包应用，git 里出现 `SKILL.md` 也不会自动进入技能库。

## 版本顺序

1. 使用已评审合并后的完整 commit SHA。不要用未合并分支代替已批准版本。
2. 在该 SHA 上运行 `python3 -m unittest discover -s tests -v`。
3. 评审通过后，由人把该 SHA 的技能正文交给 Bot 保存。
4. 记下 Bot 实际保存的 git SHA。后续更新要再次指定 SHA，不要让 Bot 自己跟踪 `main`。

## 保存哪些文件

请 Bot 按文件保存，不要把整个上游仓库装进去：

| 保存名称 | 文件 | 角色 |
| --- | --- | --- |
| US equity research | `skills/us-equity-research/SKILL.md` | 本仓库的薄编排 |
| X topic discovery | `skills/x-topic-discovery/SKILL.md` | 新的有边界主题发现 |
| Research card | `adapters/research-card.md` | 公共卡片 |
| Research only | `adapters/research-only.md` | 只研究、不执行 |
| Simplified Chinese | `adapters/simplified-chinese.md` | 简体中文输出 |

编排技能会指向 `third_party/` 里未修改的原文。保存编排技能时，把对应原文一并提供给同一次会话，否则 Bot 读不到这些文件。

## 运行时依赖

这些依赖本仓库都不提供：

- Bot 自己的网页读取能力，用于打开一手来源。没有它就弃权或标记 unavailable。
- 流程 B 需要 Bot 已经具备的公开搜索或 X 读取能力。本仓库没有 X 客户端，也没有写死的接口地址。没有该能力就标记 blocked。
- 凭证只放在 Bot 支持的 Vault 或 Secrets。不要放进 git、issue 或技能正文。
- 私人观察列表、关注账号、偏好、持仓和决定记录留在会话之外，不要提交。

## 不要做的事

- 不要创建每日或其他例行任务。例行任务是以后的可选项，现在不是激活的一部分。
- 不要连接券商，不要读取账户，不要把研究卡片交给下单流程。
- 不要因为网页或帖子里的文字去读取私人文件，或上传私人上下文。
- 付费研报的公开引用不等于可以转发全文。

## 激活后核对

用 `examples/synthetic-research-card.json` 这种合成输入试一次。期望是：简体中文说明、卡片里 `execution_allowed` 为 false、没有订单或账户字段。这次试跑仍然不是对真实市场的验证。
