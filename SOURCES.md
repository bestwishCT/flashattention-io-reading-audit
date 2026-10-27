# 来源、版本与许可

## 论文

Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudraz, Christopher Ré.
*FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness.*
arXiv:2205.14135v2 [cs.LG], 2022-06-24.
https://arxiv.org/abs/2205.14135v2
ACM/会议版本：Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudraz, Christopher Ré. *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*. NeurIPS 2022.

许可：**CC-BY 4.0**（https://creativecommons.org/licenses/by/4.0/）。

## 本包包含什么（版权合规说明）

本包**不重新分发整篇 PDF**。只包含：

| 内容 | 物理页 | 形式 |
|---|---|---|
| `FA2-P1` | 1（摘要 + 第 1 节开头） | 逐行文本 |
| `FA2-P3` | 3（贡献列表 + 硬件背景） | 逐行文本 |
| `FA2-P6` | 6（Figure 2 + Theorem 2 + Proposition 3 + 3.3 节开头） | 逐行文本 + 页图 `page6.png` |
| `FA2-P8` | 8（Table 2 + Table 3 + 4.2 节） | 逐行文本 + 页图 `page8.png` |
| （作者侧补充） | 9（Figure 3） | 仅页图 `page9.png` |

**署名与出处**：以上片段全部出自上述论文，保留原作者署名与 CC-BY 4.0 许可。本包中的原创文字与脚本以 MIT 许可发布（见 `LICENSE`）。

## 版本与校验

- 原 PDF：`research/private-originals/flashattention-v2.pdf`（本地保留，不随包分发）
- 原 PDF SHA256：`ca7f9fda10b90fc05dd291a3accc85e9c1a4a860b99b31928dab03ed3fcb14e4`
- 页码约定：`page` 是 **PDF 物理页**（从 1 开始），**不是**印刷页码。`page6.png` / `page8.png` / `page9.png` 页脚可见印刷页码 6 / 8 / 9，与物理页一致（本文正文页码与物理页码恰好对齐）。

## 抽取与修复（重要）

这份 PDF 的 Type-1 数学字体在 **pypdf** 与 **pypdfium2** 两个抽取器下都有问题：

1. **单字符错误**：pypdf 把乘号映射为 U+0002、减号为 U+0000、逗号为 U+0096、≤ 为 U+0014、数学字体括号为 U+00B9/U+00BA、地板/天花板括号错映射为无关字母。
2. **上下标降级**（更严重）：两个抽取器都把上标/下标片段拆到独立行并降级成普通数字，于是 `Θ(N²d²M⁻¹)` 变成 `Θ(N 2d2 M-1)`。

若直接把这种文本喂给模型，模型读到的是**本身就不自洽的公式**。因此：

- `normalize_pdf_text.py` 保留 pypdf 的行切分（它至少把公式留在同一行），先应用一个**显式单字符替换表**，再应用一个**按 (物理页, 行号) 定位**的 15 条公式修复表；
- 每一处修复都对照渲染出的原页图像核过（`page6.png`、`page8.png`、`page9.png`）；
- 脚本会报告"15 条修复全部命中"与残留控制字符数（当前为 0）；
- 修复**只改字符编码，不改任何数值**，属于文本重建，不是实验。

这是本项目里可复用的一个通用经验：**读到公式密集的 PDF，先验证抽取结果的字符与上下标，再决定要不要喂给模型。**

## 第三方内容

- 论文片段：Tri Dao 等，CC-BY 4.0（见上）。
- 本包中引用的复杂度记号（`Θ`、`Ω`、`o`）与 IO 概念定义均出自该论文。
- 无其它第三方数据、无凭据、无私有数据。
