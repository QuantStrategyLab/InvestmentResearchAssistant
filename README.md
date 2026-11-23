# InvestmentResearchAssistant

**尚未在 Grok Bot 中测试。** 把文件放进本仓库不会注册技能，本仓库也不会自行运行。

这是一份给 Grok Bot 使用的公开研究流程与技能配置，不是投资引擎、网站、券商接口或交易程序。第一阶段只覆盖美国股票和 ETF。研究输出固定 `execution_allowed` 为 `false`。这里没有收益承诺，也没有实时或全市场保证。

## English summary

Public, versioned research workflows for a Grok Bot. Phase 1 is US equities and ETFs. Selected MIT skill files are vendored unmodified; local files are thin adapters plus one bounded X-topic skill. Nothing here places an order. This revision has not been tested inside Grok Bot.

## 复用范围

复用的是两份已核对许可证的开源技能，加上本仓库的薄适配和新的 X 主题发现说明。这不是“市面上的主流技能都已接入”，也没有在运行时验证过这些技能会被某个 Bot 自动加载。

| 来源 | 固定提交 | 选用文件 |
| --- | --- | --- |
| [yennanliu/InvestSkill](https://github.com/yennanliu/InvestSkill) | `4d61af4ae5545a8fae8a78642c4f1a56ea3a20ec` | fact-check、earnings-preview、catalyst-calendar、bear-case、etf-analysis |
| [jaredtrichard/grok-research](https://github.com/jaredtrichard/grok-research) | `d3d4b493d4d66cc08c31e13626ac3e750613c8b2` | adversarial-review |

原文、许可证和摘要在 `third_party/` 与 `upstream/manifest.json`。个人持仓复盘和交易事后分析留到后续，本阶段不收录。

## 能做什么

既有的 QuantStrategyLab 量化或 QAR 系统可以给出标的和理由。本仓库只提供独立的研究辅助：

1. 核对一手来源。
2. 在适用时查看财报、催化剂或 ETF。
3. 做对抗性审查。
4. 给出证据卡片，由人做决定。
5. 可选地，从公开讨论里做一次有边界的主题发现，再进入同一条核对流程。

X 上的互动不是资金流。没有取回的来源不能当成“没有新闻”的证据。

## 调用示例

下面是可复制的自然语言请求，不是已注册的命令。

请只做研究，不要形成交易指令。候选标的是 SYNTH，交易所是 XNAS。先核对一手来源；如果材料属于财报、催化剂或 ETF，再使用对应的既有技能。然后做对抗性审查，并输出一张研究卡片。`execution_allowed` 必须为 false。缺少来源就弃权，不要编造数字。

从公开讨论里做一次有边界的主题发现，范围只限美国股票和 ETF。去掉重复和无法追溯的条目后，再按上面的核对流程处理。如果当前 Bot 没有可用的公开搜索，就标记为 blocked，不要编造帖子。

## 安装

人工步骤写在 [docs/install.md](docs/install.md)。顺序是：固定的 git 版本、本地确定性测试、评审与批准、再由人在支持的 Grok Bot 技能机制里显式保存该版本。本代理不能把技能装进 Bot 库。第一阶段不创建例行任务。

## 测试边界

`python3 -m unittest discover -s tests -v` 检查卡片契约、来源摘要、许可证和仓库文件。这些测试不访问网络，也不验证大模型是否听话。示例数字都是合成的，主机名是 `example.test`。

## 许可证

本仓库新写的胶水代码使用 MIT，见 [LICENSE](LICENSE)。第三方原文仍使用各自的 MIT 声明，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
