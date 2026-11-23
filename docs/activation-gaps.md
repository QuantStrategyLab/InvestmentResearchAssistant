# 激活缺口

本文件记录仓库文件做不到的事。写在这里不等于这些开关已经打开。

## 合并与风险门

这次改动包含 `.github/workflows/`、`.github/governance/`、`schema/` 和 `adapters/`。按当前策略，完整 diff 会落在 R2。宽泛的合并授权不是某一颗 head 的 R2 批准。

合并前需要两样东西，而且都要落在同一个 head SHA 上：

- 当前 head 的审查回执。回执要写明这个 SHA，审查完成，且没有未解决的发现。组织策略接受的标记包括 `ai-review-receipt:v1`、`codex-review-receipt:v1` 和 `codex-review-state:v1`。
- 一枚记在这个 head 上的放行标签。`owner-approved` 只能由所有者添加。本代理不添加、不移除该标签，也不自行合并。

`pr-template`、`ai-review`、`risk-gate` 和 `Gitleaks` 由工作流发布状态。branch protection 要另外在仓库设置里要求这些上下文，以及本仓库的 `test`，并打开 strict 与 enforce admins。只提交工作流不会启用 branch protection。

审查人身份和所有者身份来自组织变量，例如 `GOVERNANCE_REVIEWERS_JSON`、`RISK_GATE_OWNER_ID` 和 `RISK_GATE_OWNER`。本仓库的 `policy.json` 故意不写账户标识。若这些变量对该仓库不可用，门会失败关闭。本变更不读取、不创建密钥。

## secret scanning

创建仓库时，GitHub secret scanning 与 push protection 处于关闭状态。本 PR 不修改该设置。

已提交的扫描工作流：

- `gitleaks.yml` 的检查名是 `Gitleaks`，使用 PrGovernance `3d44e3d057681d5ae2730ad76af2f53b72d26767`。
- `required-gitleaks.yml` 与 `weekly-gitleaks.yml` 调用组织可复用工作流 `0da4da68433b803cda17d3f84e29875a94a32273`。检查名是 `Secret scan / Gitleaks`。周扫描不是研究例行任务；它要等文件进入默认分支并且 Actions 会跑计划任务后才会发生。

没有加入需要 `SECRET_SCAN_BASELINE_B64` 的 PrGovernance 全历史扫描，因此不新增密钥。模式扫描不能证明没有个人信息或提示注入。

`risk-gate.yml` 使用 `pull_request_target`，沿用组织副本：只读元数据，不检出 pull request 代码。其他工作流不使用 `pull_request_target`。

## Grok Bot

尚未在 Grok Bot 中测试，也没有把技能写入任何 Bot 库。激活步骤在 [install.md](install.md)。不创建 Bot routine，不部署服务，不连接券商。

## 分支

只有本任务合并之后的开发分支，在确认没有未合并提交后才可以删除。未合并时不删除。不删除其他分支。
