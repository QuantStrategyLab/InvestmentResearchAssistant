# 实现计划

目标是一个可审查的配置仓库：锁定的第三方技能、薄适配、研究卡片契约和本地测试。

## 文件

- `third_party/` 与 `upstream/manifest.json`：未修改的原文、许可证、SHA-256 和 git blob SHA-1。
- `adapters/`：简体中文、研究卡片、只研究。
- `skills/us-equity-research/SKILL.md`：编排，指向原文和适配。
- `skills/x-topic-discovery/SKILL.md`：有边界的公开讨论发现。
- `schema/research-card.schema.json` 与 `ira/card.py`：同一组必填字段。
- `ira/provenance.py` 与 `ira/hygiene.py`：摘要和明显密钥形状。
- `.github/workflows/`：组织要求的审查门、Gitleaks 和本仓库测试。

## 验证

```sh
python3 -m unittest discover -s tests -v
```

期望是全部通过，且没有网络访问。通过只说明契约测试通过。

## 不在本计划内

不合并、不打发布、不把技能写入 Bot、不创建例行任务、不读取密钥、不修改其他仓库。
