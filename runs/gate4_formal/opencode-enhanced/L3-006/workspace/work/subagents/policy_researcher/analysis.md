# Policy Version Analysis — Task L3-006

## Documents Examined

### 1. 01_expense_reimbursement_2025.md — XX证券费用报销管理办法(2025修订版)
- **发文字号**: XX证财规〔2025〕甲号
- **关键条款**:
  - 第五条: 单笔费用报销的审批权限不在本办法正文列示具体金额，统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。
  - 第十四条: 本办法自二〇二五年一月一日起施行。原《XX证券费用报销管理办法(2022版)》同时废止。

### 2. 02_expense_reimbursement_2022_deprecated.md — XX证券费用报销管理办法(2022版)
- **发文字号**: XX证财规〔2022〕乙号
- **关键条款**:
  - 第一条: 本办法为旧版，仅作制度沿革留档。现行制度以2025修订版为准。
  - 第二条: 旧版部门总经理审批线为 8000元。
  - 第三条: 旧版分管副总审批线为 30000元。
  - 第四条: 旧版审批金额已被后续制度替代，不得作为现行审批依据。

### 3. 03_authorization_management.md — XX证券授权管理办法
- **发文字号**: XX证综规〔2025〕丙号
- **关键条款**:
  - 第二条: 附件二适用于费用报销系统自动派生审批角色，相关金额为现行有效审批线。
  - 第四条: 授权调整以最新修订版附件为准。
  - 第五条: 自二〇二五年一月一日起施行。
  - **附件二 费用报销审批权限表**:
    - AR-01: 0 ≤ amount < 3000 → 部门经理
    - AR-02: 3000 ≤ amount < 10000 → 部门经理 + 财务复核
    - AR-03: 10000 ≤ amount < 50000 → **部门总经理**
    - AR-04: 50000 ≤ amount < 200000 → 分管副总
    - AR-05: amount ≥ 200000 → 总经理办公会

## Analysis

### Version Applicability
- The 2025修订版 (01_expense_reimbursement_2025.md) is the **current effective version**.
- Article 14 of the 2025修订版 explicitly states it took effect on **2025年1月1日** and **废止(abolished)** the 2022版.
- Article 1 of the 2022版 itself confirms it is only an archival record and the current system is the 2025修订版.
- Both the 2025修订版 and the 03_authorization_management have the same effective date (2025-01-01), forming a coherent current regime.

### Department General Manager (部门总经理) Approval Threshold
- **Current threshold**: 单笔金额 ≥ **10,000元** 且 < 50,000元 (AR-03 row in 附件二 of 03_authorization_management.md)
- The 2025修订版 does NOT state amounts in its own text; Article 5 delegates entirely to 03_authorization_management.md 附件二.
- The 2022版 had a different threshold of 8,000元 (Article 2), but this value is **explicitly superseded** and must not be used.

### Effective Status
| Document | Status | Effective Date | Notes |
|---|---|---|---|
| 01_expense_reimbursement_2025.md | ✅ Current / Effective | 2025-01-01 | Explicitly repealed 2022版 (Article 14) |
| 02_expense_reimbursement_2022_deprecated.md | ❌ Deprecated / Abolished | N/A | Replaced by 2025修订版; archival only |
| 03_authorization_management.md | ✅ Current / Effective | 2025-01-01 | Contains the operative approval thresholds (附件二) |

## Conclusion
The 2025修订版 applies. The department general manager approval threshold is **10,000元** (≥10000, <50000), sourced from 03_authorization_management.md 附件二, row AR-03. The old 2022版 threshold of 8,000元 is no longer valid.
