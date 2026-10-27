# 运行前核查标准

本次只研究一个论文阅读难点：把 FLOPs、HBM 访问次数、墙钟时间三者的关系读反，并把 exact / approximate 的标签安错方法。逐项检查标准如下：

1. **D1 必须读出 Fig.2 左表的三个数值并区分三个量。** Standard attention：GFLOPs 66.6、HBM R/W 40.3 GB、Runtime 41.7 ms；FlashAttention：GFLOPs 75.2、HBM R/W 4.4 GB、Runtime 7.3 ms。必须指出 FlashAttention 的 GFLOPs **更高**（因反向传播重算），HBM 访问**更少**，因此 Runtime **更短**；决定运行时间的是 HBM 访问次数，不是 FLOPs。把“FLOPs 更少所以更快”当答案即为错误。
2. **D2 必须区分三条结论。** (a) Theorem 2：标准注意力 Θ(Nd + N²) 次 HBM 访问，FlashAttention Θ(N²d²/M)（标准注意力是 Θ(Nd×N²)，注意连乘形式）。(b) Proposition 3 是**下界**：不存在算法对 M ∈ [d, Nd] 区间内所有 M 都做到 o(N²d²/M)；它不是说 FlashAttention 处处最优。论文自述为“对一个范围的 SRAM 大小是最优的”。(c) 条件涉及 d（head dim，通常 64–128）与 M（SRAM 大小，约 100KB），因为 d² ≪ M，所以访问次数少很多。若把 Proposition 3 说成“FlashAttention 对任意 M 都最优”，或把下界方向说反（说成上界），即为错误。
3. **D3 必须区分 exact 与 approximate。** FlashAttention 本身是**精确**注意力（不近似、结果与标准注意力等价）；块稀疏 FlashAttention 是**近似**方法。Table 2：GPT-2 small FlashAttention ppl 18.2、训练 2.7 天、3.5×；HuggingFace ppl 18.2、9.5 天、1.0×；Megatron-LM ppl 18.2、4.7 天、2.0×。GPT-2 medium 三者 ppl 分别为 14.2 / 14.3 / 14.3——Megatron-LM 与 FlashAttention 的 ppl 比 HuggingFace 高 0.1，属**微小质量差异**，必须如实写出，不能说“完全相同”。若说 FlashAttention 是近似方法，或漏掉 medium 的 0.1 ppl 差异，即为错误。
4. **D4 必须给出有条件结论。** (a) **不能**说 FlashAttention 降低了自注意力的时间/计算复杂度：它仍需 Θ(N²d) 计算，只是把 IO 复杂度降低；论文的 framing 是“exact + IO-aware”，与降 FLOPs 的路线正交。(b) 论文说近似注意力“many of them do not display wall-clock speedup”，是**多数**而非全部，且 Fig.2/Fig.3 显示超过 1K 之后某些近似方法（如 Linformer）开始变快——不能说“近似方法都没有墙钟加速”。(c) 块稀疏的优势与稀疏度成比例且在 seq. length 4K 下测得，不能推广到所有序列长度；第 9 页 Fig.3 的交叉点说明存在反向区间（超过某个序列长度后 FlashAttention 不再最快）。若出现“FlashAttention 把复杂度降为线性”或“近似注意力全部没有墙钟加速”，即为错误。
5. **通用检查**：行号是否在范围内且所选行真正支撑结论；是否遗漏限定条件（序列长度、GPU 型号、是否含 dropout/mask）；是否把“论文观测”写成“普遍定律”。只允许 source_id 取 FA2-P1/FA2-P3/FA2-P6/FA2-P8 四个值之一。
6. **过程纪律**：本次为一次真实调用、无对照，不声称提示词或流程带来增益。作者熟悉该论文，本次非隐藏测试、非独立复现；不得声称重新跑过论文实验。
