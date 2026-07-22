# 正式题与逐题Rubric：securities-expense-audit-formal-15-v8

Rubric版本：`atomic-binary-checklist-v6`。本文件由`runner/render_formal_cases.py`从冻结JSON生成。

## L1-001：policy_and_version

**题目：** 请依据现行制度判断单笔费用为2999.99元、3000元、9999.99元、10000元、50000元和200000元时分别需要哪些审批角色，并说明费用报销办法与授权管理办法的交叉引用关系。另请说明2022版8000元和30000元审批线是否仍适用，以及误用旧线会影响哪些金额区间。

**选题目的：** 现行审批线基础题，验证制度事实与版本意识

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `current-version` | `policy` | `hybrid` | 采用2025修订版及现行授权制度 | 明确识别现行版本，且未把2022版作为有效依据 |
| `tier-ar01` | `conclusion` | `hybrid` | 2999.99元适用AR-01部门经理审批 | 金额区间和审批角色均正确 |
| `tier-ar02-lower` | `conclusion` | `hybrid` | 3000元进入AR-02并经部门经理和财务复核 | 正确处理3000元下边界及两个必要角色 |
| `tier-ar02-upper` | `conclusion` | `hybrid` | 9999.99元仍属于AR-02 | 正确处理10000元以下的上边界 |
| `tier-ar03` | `conclusion` | `hybrid` | 10000元进入AR-03部门总经理审批 | 正确处理10000元包含边界 |
| `tier-ar04` | `conclusion` | `hybrid` | 50000元进入AR-04分管副总审批 | 正确处理50000元包含边界 |
| `tier-ar05` | `conclusion` | `hybrid` | 200000元进入AR-05总经理办公会审批 | 正确处理200000元包含边界 |
| `cross-reference-expense` | `policy` | `hybrid` | 引用费用报销办法第五条 | 准确引用费用报销办法第五条 |
| `cross-reference-authorization` | `policy` | `hybrid` | 引用授权管理办法附件二 | 准确引用授权管理办法附件二 |
| `cross-reference-relation` | `reasoning` | `hybrid` | 说明正文通过交叉引用适用附件二金额 | 准确说明两份现行制度之间的引用关系 |
| `legacy-threshold-status` | `false_positive` | `llm` | 说明2022版8000元和30000元审批线均已失效 | 两个旧值及其失效状态均说明正确 |
| `legacy-threshold-impact` | `reasoning` | `llm` | 说明误用旧线会错误升级8000至9999.99元和30000至49999.99元区间 | 两个受影响金额区间及错误升级方向均说明正确 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

## L3-006：policy_and_version

**题目：** 请判断费用报销审批线应采用2022版还是2025修订版，指出部门总经理审批线，并提供新旧版本效力状态及现行金额出处。

**选题目的：** 新旧制度冲突题，验证适用版本选择

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `current-value` | `conclusion` | `hybrid` | 现行审批线：指出2025修订版现行值 | 现行值准确 |
| `deprecated-value-amount` | `policy` | `hybrid` | 给出2022版审批线8000元 | 明确给出2022版金额8000元 |
| `deprecated-value-status` | `policy` | `hybrid` | 说明2022版已经废止 | 明确说明2022版不再有效 |
| `applicable-version` | `reasoning` | `llm` | 适用版本：明确当前应采用2025修订版 | 选择正确并说明时间适用关系 |
| `two-version-evidence-current` | `policy` | `hybrid` | 引用2025修订版的效力依据 | 引用2025修订版及其现行效力条款 |
| `two-version-evidence-deprecated` | `policy` | `hybrid` | 引用2022版的废止依据 | 引用2022版及其废止状态 |
| `two-version-evidence-amount` | `policy` | `hybrid` | 引用授权管理办法附件二的金额依据 | 引用附件二中的10000元审批档位 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

## L3-008：policy_and_version

**题目：** 分别比较差旅住宿和培训住宿的适用制度、标准维度和数值。请列出培训住宿一、二、三类城市标准，并至少举一个同城市档位下与某职级差旅标准的数值对照，说明为什么不能混用。

**选题目的：** 近似条款区分题，验证适用场景判断

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `travel-dimensions-policy` | `policy` | `hybrid` | 指出差旅住宿适用差旅费管理办法 | 正确识别差旅费管理办法 |
| `travel-dimensions-job-level` | `policy` | `hybrid` | 指出差旅住宿按员工职级区分 | 明确包含员工职级维度 |
| `travel-dimensions-city-tier` | `policy` | `hybrid` | 指出差旅住宿按城市档位区分 | 明确包含城市档位维度 |
| `training-values-policy` | `policy` | `hybrid` | 指出培训住宿适用培训费管理办法 | 正确识别培训费管理办法 |
| `training-values-tier-a` | `policy` | `hybrid` | 给出一类城市培训住宿标准500元/人/晚 | 一类城市数值和单位均正确 |
| `training-values-tier-b` | `policy` | `hybrid` | 给出二类城市培训住宿标准420元/人/晚 | 二类城市数值和单位均正确 |
| `training-values-tier-c` | `policy` | `hybrid` | 给出三类城市培训住宿标准350元/人/晚 | 三类城市数值和单位均正确 |
| `numeric-comparison-scenario` | `reasoning` | `hybrid` | 给出一个明确的城市档位和差旅职级 | 对照场景的城市档位和差旅职级均明确 |
| `numeric-comparison-travel-value` | `reasoning` | `hybrid` | 给出该场景对应的差旅住宿标准 | 差旅住宿标准与制度表一致 |
| `numeric-comparison-training-value` | `reasoning` | `hybrid` | 给出同一城市档位的培训住宿标准 | 培训住宿标准与制度表一致 |
| `numeric-comparison-same-tier` | `reasoning` | `hybrid` | 两侧数值使用同一城市档位进行比较 | 培训与差旅数值属于同一城市档位 |
| `no-mixing-scenario` | `reasoning` | `llm` | 说明培训与差旅属于不同费用事项 | 明确区分培训和差旅场景 |
| `no-mixing-dimensions` | `reasoning` | `llm` | 说明两套住宿标准的适用维度不同 | 指出培训只按城市而差旅还按职级 |
| `no-mixing-conclusion` | `reasoning` | `llm` | 明确两套标准不得混用或择高套用 | 明确作出不得混用结论 |
| `comparison-evidence-travel` | `evidence` | `hybrid` | 引用差旅费管理办法第三、四、七条 | 差旅制度及关键条款完整 |
| `comparison-evidence-training` | `evidence` | `hybrid` | 引用培训费管理办法第五、六条 | 培训制度及关键条款完整 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

## L2-003：record_audit

**题目：** 请以R000020为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 重复报销单案，验证跨记录证据关联

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `audit-conclusion` | `conclusion` | `hybrid` | 异常结论：在answer中明确判断本案构成重复报销 | answer明确认定构成重复报销且无矛盾表述 |
| `anomaly-type-count-rule-type` | `conclusion` | `deterministic` | 发现类型为DUP | 全部已提交发现均归属于DUP规则类型 |
| `anomaly-type-count-count` | `conclusion` | `deterministic` | 发现数量为1 | 已提交发现数量恰好为1 |
| `record-set-include-r000020` | `evidence` | `deterministic` | 结果包含应核查记录 R000020 | 提交的record_ids包含R000020 |
| `record-set-include-r004203` | `evidence` | `deterministic` | 结果包含应核查记录 R004203 | 提交的record_ids包含R004203 |
| `record-set-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R000020, R004203外没有其他记录 |
| `policy-basis` | `policy` | `hybrid` | 制度依据：引用01_expense_reimbursement_2025.md 第十条并说明其适用性 | 条款有效且直接支持结论 |
| `case-reasoning-same-invoice` | `reasoning` | `hybrid` | 说明两条记录使用同一发票 | 明确识别同一发票被重复使用 |
| `case-reasoning-amount` | `reasoning` | `hybrid` | 说明两条记录对应金额均为669.5元 | 金额669.5元与记录一致 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |

## L2-008：record_audit

**题目：** 请以R004212为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 拆分报销双记录案例，验证窗口和合计金额

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `audit-conclusion` | `conclusion` | `hybrid` | 异常结论：在answer中明确判断本案构成拆分报销 | answer明确认定构成拆分报销且无矛盾表述 |
| `anomaly-type-count-rule-type` | `conclusion` | `deterministic` | 发现类型为SPLIT | 全部已提交发现均归属于SPLIT规则类型 |
| `anomaly-type-count-count` | `conclusion` | `deterministic` | 发现数量为1 | 已提交发现数量恰好为1 |
| `record-set-include-r004212` | `evidence` | `deterministic` | 结果包含应核查记录 R004212 | 提交的record_ids包含R004212 |
| `record-set-include-r004213` | `evidence` | `deterministic` | 结果包含应核查记录 R004213 | 提交的record_ids包含R004213 |
| `record-set-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R004212, R004213外没有其他记录 |
| `policy-basis-expense` | `policy` | `hybrid` | 引用费用报销办法第十一条 | 引用拆分报销规则条款 |
| `policy-basis-authorization` | `policy` | `hybrid` | 引用授权管理办法附件二 | 引用10000元审批线出处 |
| `case-reasoning-window` | `reasoning` | `hybrid` | 说明两条记录位于7天窗口内 | 正确计算为7天窗口内 |
| `case-reasoning-sum` | `reasoning` | `hybrid` | 说明窗口内合计金额为10200元 | 合计金额计算为10200元 |
| `case-reasoning-threshold` | `reasoning` | `hybrid` | 说明10200元达到并超过10000元审批线 | 将合计金额与10000元审批线正确比较 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |

## L2-013：record_audit

**题目：** 请以R004223为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 培训费超标准案例，验证金额与费用类型标准

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `audit-conclusion` | `conclusion` | `hybrid` | 异常结论：在answer中明确判断本案构成超标准 | answer明确认定构成超标准且无矛盾表述 |
| `anomaly-type-count-rule-type` | `conclusion` | `deterministic` | 发现类型为OVERSTD | 全部已提交发现均归属于OVERSTD规则类型 |
| `anomaly-type-count-count` | `conclusion` | `deterministic` | 发现数量为1 | 已提交发现数量恰好为1 |
| `record-set-include-r004223` | `evidence` | `deterministic` | 结果包含应核查记录 R004223 | 提交的record_ids包含R004223 |
| `record-set-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R004223外没有其他记录 |
| `policy-basis-expense` | `policy` | `hybrid` | 引用费用报销办法第十二条 | 引用超标准总则条款 |
| `policy-basis-training` | `policy` | `hybrid` | 引用培训费管理办法第二条 | 引用3500元培训课程费标准 |
| `case-reasoning-type` | `reasoning` | `hybrid` | 说明费用类型为training_fee | 费用类型识别正确 |
| `case-reasoning-amount` | `reasoning` | `hybrid` | 说明报销金额为3700元 | 报销金额识别正确 |
| `case-reasoning-limit` | `reasoning` | `hybrid` | 说明培训课程费标准为3500元且本笔超标 | 标准及超标比较均正确 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |

## L3-001：full_year_audit

**题目：** 请对全年数据做重复报销专项扫描，按重复发票组生成稳定的发现ID，返回全部发现ID和关联record_id集合，并说明全量扫描方法和制度依据。

**选题目的：** 全年重复报销扫描，验证完整召回

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `finding-recall-50` | `evidence` | `deterministic` | 异常发现召回率达到50% | 规则计算的异常发现召回率大于等于0.50 |
| `finding-recall-80` | `evidence` | `deterministic` | 异常发现召回率达到80% | 规则计算的异常发现召回率大于等于0.80 |
| `finding-recall-100` | `evidence` | `deterministic` | 异常发现召回率达到100% | 规则计算的异常发现召回率大于等于1.00 |
| `finding-precision-50` | `false_positive` | `deterministic` | 异常发现准确率达到50% | 规则计算的异常发现准确率大于等于0.50 |
| `finding-precision-80` | `false_positive` | `deterministic` | 异常发现准确率达到80% | 规则计算的异常发现准确率大于等于0.80 |
| `finding-precision-100` | `false_positive` | `deterministic` | 异常发现准确率达到100% | 规则计算的异常发现准确率大于等于1.00 |
| `record-recall-50` | `evidence` | `deterministic` | record_id召回率达到50% | 规则计算的record_id召回率大于等于0.50 |
| `record-recall-80` | `evidence` | `deterministic` | record_id召回率达到80% | 规则计算的record_id召回率大于等于0.80 |
| `record-recall-100` | `evidence` | `deterministic` | record_id召回率达到100% | 规则计算的record_id召回率大于等于1.00 |
| `record-precision-50` | `false_positive` | `deterministic` | record_id准确率达到50% | 规则计算的record_id准确率大于等于0.50 |
| `record-precision-80` | `false_positive` | `deterministic` | record_id准确率达到80% | 规则计算的record_id准确率大于等于0.80 |
| `record-precision-100` | `false_positive` | `deterministic` | record_id准确率达到100% | 规则计算的record_id准确率大于等于1.00 |
| `finding-record-mapping-sample` | `evidence` | `hybrid` | 至少两项发现与对应record_id能够逐项复核 | 至少两项已提交发现的规则类型和record_id映射与业务数据一致；不足两项发现时要求全部一致 |
| `full-scan-method-scope` | `reasoning` | `hybrid` | 轨迹证明查询覆盖全年全部记录 | 查询或脚本覆盖完整年度而非抽样记录 |
| `full-scan-method-invoice-key` | `reasoning` | `hybrid` | 按invoice_id识别重复使用的发票 | 查询或脚本以invoice_id作为重复判断键 |
| `full-scan-method-grouping` | `reasoning` | `hybrid` | 每个重复发票组形成一项发现 | 重复记录按发票分组且每组只形成一项发现 |
| `full-scan-method-reconcile` | `reasoning` | `hybrid` | 查询结果与最终提交数量能够核对一致 | 中间统计为6组且与最终6项发现一致 |
| `policy-basis` | `policy` | `hybrid` | 制度依据：引用01_expense_reimbursement_2025.md 第十条并将规则落实到查询条件 | 条款和查询条件对应 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |
| `severe-finding-overreporting` | 提交异常发现的类型与数量精确率低于50% | 50 |

## L3-003：full_year_audit

**题目：** 请对全年数据做单笔或单次即可确认的超标准专项扫描，返回全部发现ID和关联record_id集合，并说明各费用类型的计算口径、全量扫描方法和制度依据。办公用品和通讯费用本题只识别单笔自身已经超过月度上限的明确异常，不评价多笔记录的月度累计超限。

**选题目的：** 全年超标准扫描，验证多费用类型标准

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `finding-recall-50` | `evidence` | `deterministic` | 异常发现召回率达到50% | 规则计算的异常发现召回率大于等于0.50 |
| `finding-recall-80` | `evidence` | `deterministic` | 异常发现召回率达到80% | 规则计算的异常发现召回率大于等于0.80 |
| `finding-recall-100` | `evidence` | `deterministic` | 异常发现召回率达到100% | 规则计算的异常发现召回率大于等于1.00 |
| `finding-precision-50` | `false_positive` | `deterministic` | 异常发现准确率达到50% | 规则计算的异常发现准确率大于等于0.50 |
| `finding-precision-80` | `false_positive` | `deterministic` | 异常发现准确率达到80% | 规则计算的异常发现准确率大于等于0.80 |
| `finding-precision-100` | `false_positive` | `deterministic` | 异常发现准确率达到100% | 规则计算的异常发现准确率大于等于1.00 |
| `record-recall-50` | `evidence` | `deterministic` | record_id召回率达到50% | 规则计算的record_id召回率大于等于0.50 |
| `record-recall-80` | `evidence` | `deterministic` | record_id召回率达到80% | 规则计算的record_id召回率大于等于0.80 |
| `record-recall-100` | `evidence` | `deterministic` | record_id召回率达到100% | 规则计算的record_id召回率大于等于1.00 |
| `record-precision-50` | `false_positive` | `deterministic` | record_id准确率达到50% | 规则计算的record_id准确率大于等于0.50 |
| `record-precision-80` | `false_positive` | `deterministic` | record_id准确率达到80% | 规则计算的record_id准确率大于等于0.80 |
| `record-precision-100` | `false_positive` | `deterministic` | record_id准确率达到100% | 规则计算的record_id准确率大于等于1.00 |
| `finding-record-mapping-sample` | `evidence` | `hybrid` | 至少两项发现与对应record_id能够逐项复核 | 至少两项已提交发现的规则类型和record_id映射与业务数据一致；不足两项发现时要求全部一致 |
| `full-scan-method-scope` | `reasoning` | `hybrid` | 轨迹证明查询覆盖全年全部记录 | 查询或脚本覆盖完整年度而非抽样记录 |
| `full-scan-method-approval` | `reasoning` | `hybrid` | 超标准判断排除已有专项审批的记录 | 查询或脚本仅将无专项审批的超标准记录计为异常 |
| `full-scan-method-office` | `reasoning` | `hybrid` | 办公用品按单笔600元口径核查 | 办公用品仅在单笔金额超过600元时计入 |
| `full-scan-method-communication` | `reasoning` | `hybrid` | 通讯费用按单笔300元口径核查 | 通讯费用仅在单笔金额超过300元时计入 |
| `full-scan-method-training` | `reasoning` | `hybrid` | 培训课程费按单次3500元口径核查 | 培训课程费仅在单次金额超过3500元时计入 |
| `full-scan-method-entertainment` | `reasoning` | `hybrid` | 业务招待费同时核查单次和人均标准 | 业务招待费按单次5000元和人均300元两个标准核查 |
| `full-scan-method-travel` | `reasoning` | `hybrid` | 差旅住宿按职级、城市和晚数计算 | 差旅住宿标准同时使用员工职级、城市档位和住宿晚数 |
| `full-scan-method-transport` | `reasoning` | `hybrid` | 市内交通按城市和天数计算 | 市内交通标准同时使用城市档位和出差天数 |
| `full-scan-method-reconcile` | `reasoning` | `hybrid` | 查询结果与最终提交数量能够核对一致 | 中间统计为6条且与最终6项发现一致 |
| `policy-basis-expense` | `policy` | `hybrid` | 引用费用报销办法第十二条 | 引用超标准总则条款 |
| `policy-basis-special` | `policy` | `hybrid` | 引用各费用类型对应的专项标准 | 专项标准与查询条件对应 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |
| `severe-finding-overreporting` | 提交异常发现的类型与数量精确率低于50% | 50 |

## L3-004：full_year_audit

**题目：** 请对全年数据做超预算专项扫描。按reimburse_date和record_id依次累计部门已批准费用，每个超预算部门形成1项发现，以首次使累计支出超过年度预算且无专项审批的记录作为关键record_id。请返回全部发现ID和关键record_id集合，并说明计算方法和制度依据。

**选题目的：** 全年超预算扫描，验证部门聚合

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `finding-recall-50` | `evidence` | `deterministic` | 异常发现召回率达到50% | 规则计算的异常发现召回率大于等于0.50 |
| `finding-recall-80` | `evidence` | `deterministic` | 异常发现召回率达到80% | 规则计算的异常发现召回率大于等于0.80 |
| `finding-recall-100` | `evidence` | `deterministic` | 异常发现召回率达到100% | 规则计算的异常发现召回率大于等于1.00 |
| `finding-precision-50` | `false_positive` | `deterministic` | 异常发现准确率达到50% | 规则计算的异常发现准确率大于等于0.50 |
| `finding-precision-80` | `false_positive` | `deterministic` | 异常发现准确率达到80% | 规则计算的异常发现准确率大于等于0.80 |
| `finding-precision-100` | `false_positive` | `deterministic` | 异常发现准确率达到100% | 规则计算的异常发现准确率大于等于1.00 |
| `record-recall-50` | `evidence` | `deterministic` | record_id召回率达到50% | 规则计算的record_id召回率大于等于0.50 |
| `record-recall-80` | `evidence` | `deterministic` | record_id召回率达到80% | 规则计算的record_id召回率大于等于0.80 |
| `record-recall-100` | `evidence` | `deterministic` | record_id召回率达到100% | 规则计算的record_id召回率大于等于1.00 |
| `record-precision-50` | `false_positive` | `deterministic` | record_id准确率达到50% | 规则计算的record_id准确率大于等于0.50 |
| `record-precision-80` | `false_positive` | `deterministic` | record_id准确率达到80% | 规则计算的record_id准确率大于等于0.80 |
| `record-precision-100` | `false_positive` | `deterministic` | record_id准确率达到100% | 规则计算的record_id准确率大于等于1.00 |
| `finding-record-mapping-sample` | `evidence` | `hybrid` | 至少两项发现与对应record_id能够逐项复核 | 至少两项已提交发现的规则类型和record_id映射与业务数据一致；不足两项发现时要求全部一致 |
| `full-scan-method-scope` | `reasoning` | `hybrid` | 轨迹证明按部门覆盖全年预算执行记录 | 查询或脚本覆盖全部部门的年度记录而非抽样部门 |
| `full-scan-method-grouping` | `reasoning` | `hybrid` | 费用按department_id分别累计 | 累计计算以department_id分组 |
| `full-scan-method-ordering` | `reasoning` | `hybrid` | 部门内按reimburse_date和record_id稳定排序 | 累计顺序先按reimburse_date再按record_id |
| `full-scan-method-cumulative` | `reasoning` | `hybrid` | 逐笔累计已批准费用amount | 每条关键记录的报销前后累计金额可复核 |
| `full-scan-method-crossing` | `reasoning` | `hybrid` | 选择累计首次超预算且无专项审批的记录 | 关键记录同时满足累计超过年度预算和无专项审批 |
| `full-scan-method-reconcile` | `reasoning` | `hybrid` | 每个超预算部门一项且数量与提交一致 | 中间统计为6个部门且与最终6项发现一致 |
| `policy-basis-expense` | `policy` | `hybrid` | 引用费用报销办法第十三条 | 引用超预算总则条款 |
| `policy-basis-budget` | `policy` | `hybrid` | 引用预算管理办法第二至第四条 | 引用预算约束及专项审批条款 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |
| `severe-finding-overreporting` | 提交异常发现的类型与数量精确率低于50% | 50 |

## TRAP-002：clean_trap

**题目：** 请以R004234为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 同组记录但发票不同且合计未越线

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `clean-conclusion` | `false_positive` | `hybrid` | 无异常结论：明确判断本题记录不构成异常 | 明确无异常且无矛盾表述 |
| `record-scope-include-r004234` | `evidence` | `deterministic` | 结果包含应核查记录 R004234 | 提交的record_ids包含R004234 |
| `record-scope-include-r004235` | `evidence` | `deterministic` | 结果包含应核查记录 R004235 | 提交的record_ids包含R004235 |
| `record-scope-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R004234, R004235外没有其他记录 |
| `case-specific-reason-invoice` | `reasoning` | `hybrid` | 说明两条记录发票不同 | 准确说明不构成重复发票 |
| `case-specific-reason-sum` | `reasoning` | `hybrid` | 说明7天内合计金额为500元 | 准确计算7天内合计500元 |
| `case-specific-reason-threshold` | `reasoning` | `hybrid` | 说明500元未达到10000元审批线 | 正确比较合计金额与审批线 |
| `independent-verification` | `reasoning` | `hybrid` | 在形成结论前查询线索记录及关联记录并保存可复核依据 | 工具轨迹或工作产物证明候选在结论前查询了实际记录、识别关联记录并核验适用制度；仅在最终答案复述数字不得分 |
| `policy-basis-source-1` | `policy` | `hybrid` | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十条、第十一条 | 准确引用01_expense_reimbursement_2025.md#第十条、第十一条 |
| `policy-basis-source-2` | `policy` | `hybrid` | 引用本题所需制度依据：03_authorization_management.md#附件二 | 准确引用03_authorization_management.md#附件二 |
| `no-unsupported-output` | `false_positive` | `deterministic` | 结构化结果不提交任何异常ID | anomaly_ids为空 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `substantive-false-positive` | 将无异常案例提交为实质异常 | 40 |

## TRAP-003：clean_trap

**题目：** 请以R004236为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 超过聚合时间窗，验证窗口边界

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `clean-conclusion` | `false_positive` | `hybrid` | 无异常结论：明确判断本题记录不构成异常 | 明确无异常且无矛盾表述 |
| `record-scope-include-r004236` | `evidence` | `deterministic` | 结果包含应核查记录 R004236 | 提交的record_ids包含R004236 |
| `record-scope-include-r004237` | `evidence` | `deterministic` | 结果包含应核查记录 R004237 | 提交的record_ids包含R004237 |
| `record-scope-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R004236, R004237外没有其他记录 |
| `case-specific-reason-gap` | `reasoning` | `hybrid` | 说明两条费用发生日期相隔8天 | 日期间隔计算为8天 |
| `case-specific-reason-window` | `reasoning` | `hybrid` | 说明8天超出7天聚合窗口 | 正确应用7天窗口边界 |
| `case-specific-reason-sum` | `reasoning` | `hybrid` | 说明两条记录合计金额为10400元 | 准确计算合计金额10400元 |
| `case-specific-reason-threshold` | `reasoning` | `hybrid` | 说明10400元虽达到10000元审批线但因超窗不构成拆分 | 正确说明金额条件满足但时间窗口条件不满足 |
| `independent-verification` | `reasoning` | `hybrid` | 在形成结论前查询线索记录及关联记录并保存可复核依据 | 工具轨迹或工作产物证明候选在结论前查询了实际记录、识别关联记录并核验适用制度；仅在最终答案复述数字不得分 |
| `policy-basis-source-1` | `policy` | `hybrid` | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十一条 | 准确引用01_expense_reimbursement_2025.md#第十一条 |
| `policy-basis-source-2` | `policy` | `hybrid` | 引用本题所需制度依据：03_authorization_management.md#附件二 | 准确引用03_authorization_management.md#附件二 |
| `no-unsupported-output` | `false_positive` | `deterministic` | 结构化结果不提交任何异常ID | anomaly_ids为空 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `substantive-false-positive` | 将无异常案例提交为实质异常 | 40 |

## TRAP-005：clean_trap

**题目：** 请以R004239为线索，结合现行制度和业务数据核查相关费用记录是否存在异常。请返回核查涉及的record_id集合、审计结论、关键事实和制度依据；如存在异常，再返回发现ID。

**选题目的：** 多条件均合规，验证综合反向复核

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `clean-conclusion` | `false_positive` | `hybrid` | 无异常结论：明确判断本题记录不构成异常 | 明确无异常且无矛盾表述 |
| `record-scope-include-r004239` | `evidence` | `deterministic` | 结果包含应核查记录 R004239 | 提交的record_ids包含R004239 |
| `record-scope-include-r004240` | `evidence` | `deterministic` | 结果包含应核查记录 R004240 | 提交的record_ids包含R004240 |
| `record-scope-no-extra` | `evidence` | `deterministic` | 结果不包含本题范围外的记录 | 提交的record_ids除R004239, R004240外没有其他记录 |
| `case-specific-reason-business-context` | `reasoning` | `hybrid` | 说明两条记录对应不同客户和不同业务事项 | 准确区分两次独立业务活动 |
| `case-specific-reason-date-window` | `reasoning` | `hybrid` | 说明两条费用发生日期相隔1天并完成窗口核查 | 准确核对日期间隔及7天窗口 |
| `case-specific-reason-invoice` | `reasoning` | `hybrid` | 说明两条记录发票不同 | 准确排除重复发票 |
| `case-specific-reason-amounts` | `reasoning` | `hybrid` | 给出单次金额540元和545元 | 两笔金额均准确 |
| `case-specific-reason-participants` | `reasoning` | `hybrid` | 说明两次活动均为3人 | 参与人数准确 |
| `case-specific-reason-per-capita` | `reasoning` | `hybrid` | 计算人均180元和约181.67元 | 两笔人均金额均准确 |
| `case-specific-reason-standard` | `reasoning` | `hybrid` | 说明单次金额和人均金额均未超过招待费标准 | 正确比较单次5000元和人均300元标准 |
| `case-specific-reason-split` | `reasoning` | `hybrid` | 说明两笔合计未达到10000元审批线 | 正确排除拆分规避审批 |
| `independent-verification` | `reasoning` | `hybrid` | 在形成结论前查询线索记录及关联记录并保存可复核依据 | 工具轨迹或工作产物证明候选在结论前查询了实际记录、识别关联记录并核验适用制度；仅在最终答案复述数字不得分 |
| `policy-basis-source-1` | `policy` | `hybrid` | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十条、第十一条 | 准确引用01_expense_reimbursement_2025.md#第十条、第十一条 |
| `policy-basis-source-2` | `policy` | `hybrid` | 引用本题所需制度依据：06_business_entertainment.md#第二条至第四条 | 准确引用06_business_entertainment.md#第二条至第四条 |
| `policy-basis-source-3` | `policy` | `hybrid` | 引用本题所需制度依据：03_authorization_management.md#附件二 | 准确引用03_authorization_management.md#附件二 |
| `no-unsupported-output` | `false_positive` | `deterministic` | 结构化结果不提交任何异常ID | anomaly_ids为空 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `substantive-false-positive` | 将无异常案例提交为实质异常 | 40 |

## L3-007：retrieval_and_report

**题目：** 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

**选题目的：** 二跳制度检索，验证交叉引用

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `threshold-amount` | `conclusion` | `hybrid` | 给出部门总经理审批线10000元 | 明确给出金额10000元 |
| `threshold-inclusive` | `conclusion` | `hybrid` | 说明达到10000元即进入该审批档位 | 明确说明包含10000元边界 |
| `two-hop-path-first` | `reasoning` | `hybrid` | 第一跳定位费用报销办法第五条 | 识别第一跳制度和条款 |
| `two-hop-path-relation` | `reasoning` | `hybrid` | 识别第五条指向授权管理办法附件二 | 明确说明制度间交叉引用关系 |
| `two-hop-path-second` | `reasoning` | `hybrid` | 第二跳定位授权管理办法附件二 | 完成第二跳检索 |
| `citations-expense` | `policy` | `hybrid` | 引用费用报销办法第五条 | 引用第一跳制度及条款 |
| `citations-authorization` | `policy` | `hybrid` | 引用授权管理办法附件二 | 引用第二跳制度及附件 |
| `no-premature-stop` | `false_positive` | `llm` | 检索完整性：不因首份制度未列金额而提前结束 | 轨迹证明继续检索 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

## L3-009：retrieval_and_report

**题目：** 请基于全年数据形成费用异常审计摘要，覆盖重复报销、拆分报销、超标准、超预算和超期报销五类规则。发现口径为：重复报销按重复发票组计1项；拆分报销按同一员工、同一费用类型7天窗口聚合组计1项；超标准只计单笔或单次即可确认的异常，办公用品和通讯费用不评价多笔月度累计；超预算按部门计1项，以按reimburse_date和record_id累计时首次使累计支出超过预算且无专项审批的记录作为关键记录；超期报销按记录计1项。请按规则类型生成稳定的发现ID，说明各类发现数量，在record_ids中返回全部异常发现涉及的记录，并在审计说明中至少逐类给出一个发现与record_id的对应示例，同时说明制度依据、影响和建议；不得把仅接近阈值但实际合规的记录计入异常。

**选题目的：** 全年综合报告，验证五类规则汇总

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `finding-recall-50` | `evidence` | `deterministic` | 异常发现召回率达到50% | 规则计算的异常发现召回率大于等于0.50 |
| `finding-recall-80` | `evidence` | `deterministic` | 异常发现召回率达到80% | 规则计算的异常发现召回率大于等于0.80 |
| `finding-recall-100` | `evidence` | `deterministic` | 异常发现召回率达到100% | 规则计算的异常发现召回率大于等于1.00 |
| `finding-precision-50` | `false_positive` | `deterministic` | 异常发现准确率达到50% | 规则计算的异常发现准确率大于等于0.50 |
| `finding-precision-80` | `false_positive` | `deterministic` | 异常发现准确率达到80% | 规则计算的异常发现准确率大于等于0.80 |
| `finding-precision-100` | `false_positive` | `deterministic` | 异常发现准确率达到100% | 规则计算的异常发现准确率大于等于1.00 |
| `record-recall-50` | `evidence` | `deterministic` | record_id召回率达到50% | 规则计算的record_id召回率大于等于0.50 |
| `record-recall-80` | `evidence` | `deterministic` | record_id召回率达到80% | 规则计算的record_id召回率大于等于0.80 |
| `record-recall-100` | `evidence` | `deterministic` | record_id召回率达到100% | 规则计算的record_id召回率大于等于1.00 |
| `record-precision-50` | `false_positive` | `deterministic` | record_id准确率达到50% | 规则计算的record_id准确率大于等于0.50 |
| `record-precision-80` | `false_positive` | `deterministic` | record_id准确率达到80% | 规则计算的record_id准确率大于等于0.80 |
| `record-precision-100` | `false_positive` | `deterministic` | record_id准确率达到100% | 规则计算的record_id准确率大于等于1.00 |
| `representative-evidence-dup` | `evidence` | `hybrid` | DUP类至少有1个可复核发现及record_id | DUP类同时给出稳定发现ID和正确record_id证据 |
| `representative-evidence-split` | `evidence` | `hybrid` | SPLIT类至少有1个可复核发现及record_id | SPLIT类同时给出稳定发现ID和正确record_id证据 |
| `representative-evidence-overstd` | `evidence` | `hybrid` | OVERSTD类至少有1个可复核发现及record_id | OVERSTD类同时给出稳定发现ID和正确record_id证据 |
| `representative-evidence-budget` | `evidence` | `hybrid` | BUDGET类至少有1个可复核发现及record_id | BUDGET类同时给出稳定发现ID和正确record_id证据 |
| `representative-evidence-overdue` | `evidence` | `hybrid` | OVERDUE类至少有1个可复核发现及record_id | OVERDUE类同时给出稳定发现ID和正确record_id证据 |
| `policy-coverage-expense` | `policy` | `hybrid` | 引用费用报销办法中五类规则的对应条款 | 费用报销办法规则条款可核查 |
| `policy-coverage-special` | `policy` | `hybrid` | 超标准结论引用对应专项费用标准 | 专项费用标准与超标准发现对应 |
| `policy-coverage-budget` | `policy` | `hybrid` | 超预算结论引用预算管理办法 | 预算管理条款可核查 |
| `clean-boundary-control` | `false_positive` | `deterministic` | 不得将已知合规边界记录计入异常结果 | 提交的record_ids不包含任何已知合规边界记录 |
| `report-shape-fact` | `reasoning` | `llm` | 报告包含事实 | 报告中存在可识别的事实内容 |
| `report-shape-rule` | `reasoning` | `llm` | 报告包含规则 | 报告中存在可识别的规则内容 |
| `report-shape-judgment` | `reasoning` | `llm` | 报告包含判断 | 报告中存在可识别的判断内容 |
| `report-shape-impact` | `reasoning` | `llm` | 报告包含影响 | 报告中存在可识别的影响内容 |
| `report-shape-recommendation` | `reasoning` | `llm` | 报告包含建议 | 报告中存在可识别的建议内容 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |

**严重错误封顶：**

| ID | 条件 | 分数上限 |
| --- | --- | ---: |
| `severe-record-overreporting` | 提交记录集合精确率低于50% | 50 |
| `severe-finding-overreporting` | 提交异常发现的类型与数量精确率低于50% | 50 |

## L3-010：retrieval_and_report

**题目：** 请形成一段制度版本风险审计说明：列明2022版与2025现行审批线及效力状态，按金额区间说明继续使用旧版会产生哪些错误升级或漏升级风险，并给出可执行的版本校验控制。结论必须引用费用报销办法与授权管理办法的现行交叉依据。

**选题目的：** 制度版本风险报告，验证审计表达

| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |
| --- | --- | --- | --- | --- |
| `current-version` | `conclusion` | `hybrid` | 说明2025修订版为现行版本 | 明确识别现行版本及其效力 |
| `current-threshold-gm` | `conclusion` | `hybrid` | 给出现行部门总经理审批线10000元 | 正确给出10000元包含边界 |
| `current-threshold-vp` | `conclusion` | `hybrid` | 给出现行分管副总审批线50000元 | 正确给出50000元包含边界 |
| `legacy-threshold-gm` | `policy` | `hybrid` | 给出2022版部门总经理审批线8000元 | 正确给出旧版8000元审批线 |
| `legacy-threshold-vp` | `policy` | `hybrid` | 给出2022版分管副总审批线30000元 | 正确给出旧版30000元审批线 |
| `legacy-status` | `false_positive` | `llm` | 说明2022版审批金额已被替代且不得作为现行依据 | 明确排除旧版金额的现行适用性 |
| `cross-reference-expense` | `policy` | `hybrid` | 引用费用报销办法第五条和第十四条 | 准确引用现行办法的交叉引用和废止条款 |
| `cross-reference-authorization` | `policy` | `hybrid` | 引用授权管理办法附件二 | 准确引用现行审批金额表 |
| `impact-lower-band` | `reasoning` | `llm` | 说明8000至9999.99元会被旧线错误升级 | 明确给出受影响区间及错误升级方向 |
| `impact-upper-band` | `reasoning` | `llm` | 说明30000至49999.99元会被旧线错误升级 | 明确给出受影响区间及错误升级方向 |
| `unaffected-band` | `reasoning` | `llm` | 说明10000至29999.99元的新旧必要最高审批角色一致 | 正确识别新旧规则在该区间不会改变最高审批角色 |
| `version-control` | `reasoning` | `llm` | 提出同时校验生效日期、废止关系和交叉引用目标的控制 | 控制措施覆盖版本元数据、废止状态和引用目标，不只是泛泛提出加强管理 |
| `submission` | `format` | `deterministic` | 统一Schema结果提交成功 | 提交回执状态为accepted且Schema校验通过 |
