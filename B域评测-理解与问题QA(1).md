# B 域黑盒横评 · 理解与问题 Q&A

> 对同事交付的 B 域费用审计横评(仓库 `blackbox-eval`)的逐问拆解与问题排查记录。
> 语料/题集/数据已随仓库到位(`data/`),GATE 1–4 baseline 已跑完。
> 配置要点:模型 `deepseek-v4-flash`(云端 DeepSeek API,**偏离 spec"仅本地模型"铁律,标注为 user-approved**);判卷 GATE4 改用 **LLM judge**;4 候选 × **55 题 × 3 变体 × 1 次 = 165 结果/候选**。
> 配套流程图 Artifact:各任务类型"从题面到输出"的期望行为流程(见对话内链接)。

---

## Q1 · GATE 1/2/3/4 分别是什么

四道**递进的人工闸门**,承诺度逐级加大,每道停下等人工确认才进下一道:

| GATE | 关卡问题 | 同事实际做的 | 产物 |
|---|---|---|---|
| **1 夹具就绪** | 两个 MCP 工具建好、每个工具能正常调用吗? | `policy_query_mcp`(4 工具)+ `expense_query_mcp`(7 工具)逐个手工调一次全 ok;过关后**夹具冻结** | `gate1_fixture_check.md` |
| **2 候选接入+金丝雀** | 4 候选装好、原生编码工具真禁了、只剩两个 MCP 吗? | 4 候选装配+版本 pin;三金丝雀 `canary-bash`(拒绝 shell)/`canary-write`(写不了、workdir diff 空)/`canary-mcp`(能调 MCP)全过 | `gate2_candidate_check.md`、`runs/gate2/` |
| **3 冒烟(判卷确认点)** | 烧钱跑全量前,单候选跑几题走通全链路,人工确认**判卷是对的** | goose 跑 L1-001/002/003(执行→采集→判卷→单页报告);暴露问题后迭代修复再冒烟 | `gate3_smoke_report.md`、`gate3_fixed_*` |
| **4 全量 baseline** | 全量跑、只监控不干预、出报告 | 4 候选 × 55×3×1;主结果+行为差异+失败归因 | `gate4_baseline_report.md`、`gate4_failure_attribution.jsonl` |

一句话:**GATE1 工具就绪 → GATE2 候选接入且安全 → GATE3 判卷可信 → GATE4 全量出分**。

---

## Q2 · L1/L2/L3 三种任务分型

按**任务复杂度/所需能力**分层(与 category 正交:level 管难度,category 管题型)。B 域是费用审计,梯度锚在"检索一个事实 → 制度对数据找异常 → 全量深度审计":

| level | 数量 | 能力 | category | 判分 kind |
|---|---|---|---|---|
| **L1** 单点检索 | 15 | 一次查询答一个事实 | policy_qa / single_anomaly_lookup / ground_truth_lookup / version_check | `expected_facts` |
| **L2** 制度×数据比对(核心) | 25 | 拉制度规则+业务数据交叉核对,定位**一个**异常 | 全是 policy_data_comparison | `anomaly_id_set` |
| **L3** 全量/多跳/版本/报告 | 10 | 深度编排+抗 context 压力 | full_year_rule_audit / two_hop_retrieval / version_trap / near_clause_disambiguation / audit_report | 大集合 `anomaly_id_set` / `expected_facts` |
| **trap** 干净但可疑 | 5 | 该说"无异常"时别乱报(反幻觉) | clean_but_suspicious | `no_anomaly` |

梯度:L1 查一个事实 → L2 制度对数据找**一个**异常 → L3 全量找**全部**异常/多跳/版本 → trap 别脑补异常。
(对照 A 域:A 域按条款检索难度分 L1 单条款/L2 双条款/L3 版本二跳歧义;两域 scoring 结构因此不同。)

---

## Q3 · 如何判别智能体完成任务的优劣

不是一个分数,是"格式闸门 + 双轨判分 + 多维指标 + 失败归因"体系。

**第 0 层 格式闸门**:答案必须是可解析 JSON `{"anomaly_ids","answer","citations"}`;解析不出记 `format_failure`、该题 0 分。

**第 1 层 双轨判分**(`grade.py`):
- **确定性 `rule_grade`**(二元 1/0,all-or-nothing):`anomaly_id_set`(预测异常集**与真值完全相等**才 1 分,另算 precision/recall)、`record_id_set`(异常集且记录集都对)、`expected_facts`(全部必要事实命中**且**引用正确)、`no_anomaly`(期望空异常集)。
- **LLM judge**(语义判分):用**同一 deepseek endpoint 当判官**,产出 judge_reason/confidence/missing/extra,比精确集合匹配宽容。**GATE4 主分用的是它**;确定性指标与格式并列跟踪。

**第 2 层 多维指标矩阵**:总分+分 level+分变体(鲁棒性)/ format_ok / clean_workdir / artifacts / timeouts / avg_tool_calls / avg_policy_calls / avg_expense_calls / **deprecated_citations(引废止版次数)** / 失败归因分层。

**⚠️ 可信度关键点**:
1. 确定性判分极严(集合差一个即 0)→ 故加 LLM judge 兜语义。
2. **judge 同源偏置**:判官与候选都用 deepseek,削弱可比性(spec 本要"纯确定性判卷"正为避此)。
3. **格式拖累分数**:llm_score 可高于操作层 ok 数——语义对但格式坏的答案 judge 仍给分、确定性轨判 0;故 format 单列。看推理看 llm_score,看规范看 format_ok。

---

## Q4 · 各任务类型的期望行为流程

见配套流程图 Artifact。要点(源自 `audit_role_prompt.md` + `grade.py` + `evals.json`):
- **贯穿铁律**:先制度依据 → 再业务事实 → 给结论。
- **L1** 单域单跳;**L2(核心)** policy 取规则 × expense 取事实 → 比对定位一个异常;**L3** 全量分页扫/二跳/版本红线(引废止版判错→deprecated_citations)/条款消歧/报告;**trap** 看着可疑实则合规 → 正确答案是空异常集,报了就是假阳性。
- 工具序列是**期望**路径,候选实际路径看各自 trajectory。

---

## Q5 · 大部分任务失败的原因

488 个失败(660 次运行,ok 仅 172=26%):

| 失败层 | 数量 | 性质 |
|---|---|---|
| **format_failure** | **324(66%)** | 主导——没产出可解析 JSON |
| record_id_miss | 49 | 能力:记录集不全 |
| no_anomaly_false_positive | 47 | 能力:过度报异常/脑补违规 |
| reasoning_or_retrieval_error | 37 | 能力:判错、record_id 当 anomaly_id |
| fact_miss | 26 | 能力:漏必要事实 |
| timeout / rubric_miss | 5 | 可忽略 |

**关键结论:大部分失败是"格式没遵守",不是"不会做题"。** format_failure 两种成因:
- **答案对、JSON 写坏**(qwen 为主):塞了 `\n`/markdown/内层双引号 → 解析失败。
- **根本没吐 JSON**(trae 127、goose 104):撞 max-steps 或只吐散文没吐 JSON 块。

按候选:goose/trae 几乎全栽格式/步数(低分**不是推理差**);qwen/opencode 格式失败少,失败更多在假阳性+record_id 漏(真·推理短板)。

**含义**:当前 baseline 排名很大程度在测"守不守 JSON 契约",而非审计推理本身——故同事把 format_ok 单列 + 改 LLM judge。看真实推理要看 llm_score。

---

## Q6 · 超出步数限制的具体原因(是循环思考吗)

**不是循环思考。** 主要受害者 **trae(135/165=82% 以"exceeded maximum steps"收尾)**,三个叠加原因:

1. **步数上限太低(max_steps=6–8)配不上任务**:L3 全量题要分页翻整年(`list_expenses×5+`),8 步翻不完就撞墙;L2 多记录比对常需 >8 步。
2. **在追一个查不到的"异常ID"**:L1-006 证据步1–3 已够,步4–8 反复 `search_policy("异常ID 重复报销 A001")` 想在制度库找 DUP-001 这种标签——**已核实查不到**(expense 表无该字段、语料无、spec 禁异常原语)→ 空耗到撞墙。
3. **SWE 框架非 task_done 不可、不肯早收尾**:trae 本质是解 repo issue 的软件工程 agent(system prompt 把审计题包装成"solving the issue in our repository"),必须最后显式调 `task_done` 交 JSON;倾向"再多查点"而非"就手头证据收尾"→ 步数耗尽=永远没吐 JSON=format_failure。

**确定不是空想的证据**:L1-006 全程仅 24 秒;每步调用的工具/参数都不同;L2-001 正好 8 步走完并 task_done、输出合法 JSON——**装得下就做得对**,纯预算问题。
(goose 的格式失败是另一回事:最终消息里没有契约 JSON;qwen 是 JSON 被写坏。只有 trae 是步数主导。)

---

## Q7 · 如何归因:问题在 agent / 大模型 / 任务本身

一个低分叠了四层:**任务/夹具、base 大模型、agent/harness、判分器**。判别第一性原理=**控制变量,一次只动一层**。本评测已固定"同模型+冻结夹具+同题",**只放开 harness**。

**落刀决策树:**
1. **失败层先分流**:`format_failure/timeout` → 几乎必是 harness/管道(已坐实:trae 步数、goose 格式、qwen JSON 坏)。`reasoning/fact/record/false_positive` → 进下一刀。
2. **跨候选一致性**:同题有过有挂 → **harness 差异**;同题全挂 → 进探针。
3. **天花板/参照解题探针**(区分"题坏/题难/模型不够"的关键):用强模型+充足步数+干净 I/O 对着真值解——
   - 连理想条件都够不到真值 → **任务/夹具坏**(铁证:anomaly_id 不可检索 → 确定性 anomaly_id 匹配本质不可赢)。
   - 能解但需更强模型 → **base 模型天花板**。
   - 轻松能解候选却挂 → 回查 harness/判分。
4. **判分器反查**:抽"判 0 但其实对"的样本,防止格式闸门/精确匹配冤判上游。
5. **变体敏感度**:只在 distracted 挂 → 鲁棒性(harness+模型),非题无效。

**本评测能/不能分清**:
- ✅ 能干净归因到 **harness**(靠跨候选控制变量)。
- ❌ 分不清"**模型天花板 vs 题太难**"——因为**只跑了一个模型**;要拆需换模型重跑(分数跳=模型受限,平=脚手架/题封顶)。
- ⚠️ 缺一个独立**参照解题器**(GATE4 只有判官,没有满血 solver 证明每题可解性)——这正是 A 域对抗验证/天花板基线要干的事,B 域缺此环。

---

## Q8 · MCP 层是否满足需求 / 是否制约了模型

**定性:MCP 写得不糙**(只读、过滤、分页带 total、逐任务日志、`get_expense_detail` 一把抓、`find_invoice_usage` 即查重原语,遵循"不给检测原语"哲学)。问题不是代码错,是**能力面配不配得上任务**。

- **✅ L1/L2 定向题——够用**:给线索时能取规则+抓事实+查发票复用+查预算+查审批,重复/拆分/超档/超预算都查得到。这里失败主因是 harness+判分,不是 MCP。
- **❌ L3 全量审计——结构性不够(真瓶颈)**:硬数据 **4240 条记录 / 4234 张发票 / 仅 6 张被复用 / 全量翻 85 页**;expense MCP **无任何枚举/聚合原语**(无 list_invoices、无"查复用发票"、无 group-by、无排序、无"缺审批"过滤)。"全年找出所有重复"只能翻 85 页把 4240 发票号全记进 context 再手找 6 个——**任何合理预算下不可行**。设计砍掉"检测捷径"(对)但把"高效枚举"也一起砍了(过头)。这使 L3 各家全崩,根子在 MCP 粒度,非模型/harness。

**次要弱点**:
1. policy 检索**单字分词**(逐汉字)→ BM25 排序粗;好在 20 篇小库 + `get_policy_doc` 全文兜底,不致命。
2. **版本无结构化元数据**(现行/废止靠文件名 `_deprecated`/正文认)。
3. **anomaly_id 不可检索**,判分却精确匹配 → MCP↔判分契约错位。
4. 性能:policy 每调重算全库 BM25;expense 每页 50×13 字段大 JSON → 放大 L3 的 context 压力。
5. 无发票侧入口(find_invoice_usage 须先知 invoice_no)。

**结论**:MCP 不足**确实制约模型,但集中在 L3(10/55 题)**;L1/L2 够用。属"任务↔夹具契约不匹配"层,可由参照解题探针坐实。

**修复建议**:
- expense:补 `list_invoices`/`find_reused_invoices`、按金额/日期排序、过滤"缺审批"、或加大页/给候选集。
- policy:词级分词(jieba/2-gram)+ 结构化版本字段(status/effective_date)。
- anomaly_id:要么可检索,要么判分不强制精确匹配(改判 record_id 集合)。

---

## 附:baseline 主结果(LLM judge 语义分)

| 候选 | 版本 | 总分 | L1 | L2 | L3 | TRAP | format_ok | 主导失败 |
|---|---|---|---|---|---|---|---|---|
| qwen-code | 0.19.6 | 39.4% | 62% | 31% | 43% | 7% | 74% | format40 / 假阳性24 |
| opencode | 1.17.14 | 37.6% | 36% | 47% | 30% | 13% | 68% | format53 / record_id24 |
| goose | 1.41.0 | 25.5% | 38% | 17% | 30% | 20% | 37% | **format104** |
| trae-agent | 0.1.0 | 18.8% | 31% | 9% | 27% | 13% | 22% | **format127(步数)** |

---

## 附:发现的问题清单(可作给同事的修复项)

| # | 层 | 问题 | 影响 | 建议 |
|---|---|---|---|---|
| P1 | 夹具/判分 | **anomaly_id 不可检索**却要精确匹配 | 检测题确定性判分近乎不可赢;trae 空耗步数追它 | 让其可检索 或 改判 record_id 集合 |
| P2 | harness | trae **max_steps=6–8 太低** + 必须 task_done | trae 135/165 撞上限、18.8% 严重低估 | 步数提到 30–40;允许用手头证据早收尾 |
| P3 | 夹具 | **expense MCP 无枚举/聚合原语** | L3 全量审计结构性不可行 | 补 list_invoices/find_reused_invoices/排序/过滤 |
| P4 | harness | goose/qwen **输出契约遵循差**(没吐/写坏 JSON) | format_failure 占 66% 失败,拖累分数 | 加输出后处理/重试;或判分容忍 |
| P5 | 判分 | **LLM judge 同源偏置**(判官=候选模型) | 削弱跨候选可比性 | 判官换不同家族模型 或 回归确定性为主 |
| P6 | 方法 | **只跑单模型**,分不清模型天花板 vs 题太难 | 归因不完整 | 补换模型重跑 + 参照解题器 |
| P7 | 夹具 | policy 单字分词 + 无版本元数据 | 检索粗、版本题靠眼力 | 词级分词 + status/effective_date 字段 |
| P8 | 合规 | 走云端 DeepSeek(偏离本地-only)、模型名 `deepseek-v4-flash` 待核 | 与 spec 铁律不符 | 确认授权与模型名 |
