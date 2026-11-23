# 研究卡片

这是适配说明，不是对 `third_party/` 原文的修改。

每份研究结束时给出一张卡片，字段为：

- `as_of`
- `source_times`：`published` 与 `retrieved` 分开
- `ticker` 与 `exchange`
- `claim`
- `evidence_state`：`supported`、`unavailable`、`blocked`、`stale`、`rumor`、`duplicate`、`contradicted` 或 `abstain`
- `primary_evidence`：可点击的精确 https URL
- `counter_evidence`
- `confidence_reason`：用句子说明理由，不写单独的概率或 HIGH/MEDIUM/LOW 分数
- `missing_data`
- `invalidation`
- `next_review`
- `execution_allowed`：只能是布尔值 false

财务数字放在 `financial_figures`，每项都要有 `source_url`、`published_at` 和 `retrieved_at`。没有来源就不要写数字。

同一 ticker 必须带交易所。转载写入 `canonical_url`，并把状态设为 `duplicate`。取不到来源时，在 `missing_data` 写明这不能证明没有新闻。

不要添加订单、账户、持仓或目标股数字段。
