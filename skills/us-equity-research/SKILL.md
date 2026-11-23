---
name: US equity research
description: Research-only workflow for one US equity or ETF. Use when a person supplies a ticker and exchange or an existing candidate note. Not a trading skill.
---

# US equity research

尚未在 Grok Bot 中测试。保存本文件不会自动注册技能。

## 何时使用

人给出美国股票或 ETF 的 ticker 和交易所，或给出一份旧的候选说明。不要在没有交易所的情况下开始。不要用它处理其他市场。

## 读取

先读这些适配，再按需读取未修改的原文：

- `adapters/research-only.md`
- `adapters/research-card.md`
- `adapters/simplified-chinese.md`
- `third_party/investskill/plugins/us-stock-analysis/skills/fact-check/SKILL.md`
- 财报材料再读 `earnings-preview/SKILL.md`
- 事件日历再读 `catalyst-calendar/SKILL.md`
- ETF 再读 `etf-analysis/SKILL.md`
- 相反证据读 `bear-case/SKILL.md`
- 最后读 `third_party/grok-research/skills/adversarial-review/SKILL.md`

路径都相对于本仓库。原文与适配冲突时，以适配为准。不要把六份技能全部跑完。

## 输出

一张研究卡片。`execution_allowed` 为 false。缺来源就弃权。不要编造价格或财务数字。

## 不做

不创建订单，不读取账户，不把卡片提交到交易系统，不打开 pull request，不创建例行任务。
