# 面向具身智能的数据准备：原始论文 PDF 包

生成日期：2026-08-01

## 本包包含什么

- 54 篇可公开获取的原始论文 PDF：覆盖论文笔记库中的 50 个条目、3 篇相邻领域综述；P204 以 DataComp 与 JEST 两篇代表作共同展开。
- PDF 已按研究主题分为 6 个目录。
- `manifests/included_pdfs.csv`：已收录论文、页数、文件大小、arXiv ID、来源页面与 SHA-256。
- `manifests/all_204_note_entries.csv`：论文笔记库全部 204 个条目及本次是否收录 PDF。
- `manifests/not_bundled_in_this_pass.csv`：本次没有收入 PDF 的条目。
- `manifests/SHA256SUMS.txt`：文件完整性校验。
- `manifests/searches/2026-08-01/`：DBLP/arXiv 的原始检索响应、逐查询状态、定向重试和解析后的结果；28 个查询最终均成功，得到 1,160 条标题去重的发现记录。
- `scripts/download_core_papers.py` 与 `scripts/update_pdf_manifests.py`：可重复下载核心原文并重建页数、大小与哈希清单。

## 范围说明

上一轮调研主要通过在线页面与原文内容阅读，并没有把 204 个条目的 PDF 全部保存到本地。本次补抓了 Survey 正文实际引用的全部 arXiv 原文，并补充了用于界定边界的相邻综述，因此本包仍不是“204 篇全集”。其余条目中还包含网页技术报告、数据格式/平台、摘要级扩展索引，以及尚未在笔记中记录稳定 PDF 地址的论文。

本包中的 54 个 PDF 均已通过 `pdfinfo` 解析、页数和文件大小检查；未发现损坏或零页文件。`included_pdfs.csv` 与 `SHA256SUMS.txt` 由脚本从文件本身重建。PDF 的著作权与许可仍归原作者和发布平台所有，仅按公开来源整理，适合个人研究与文献管理使用。

## 完整包额外内容

`survey_and_notes/` 同时包含中文 Survey 初稿与 204 项结构化论文笔记。
