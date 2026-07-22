# Policy Researcher Analysis: Version Trap in XX Securities Approval Thresholds

**Task:** L3-010 — Analyze the version trap between 2022 (deprecated) and 2025 (current) expense reimbursement approval thresholds.

**Date of Analysis:** 2026-07-21

---

## 1. Documents Reviewed

| Doc ID | Title | Ref No. | Status |
|--------|-------|---------|--------|
| `01_expense_reimbursement_2025.md` | XX证券费用报销管理办法(2025修订版) | XX证财规〔2025〕甲号 | **Current / Effective** |
| `02_expense_reimbursement_2022_deprecated.md` | XX证券费用报销管理办法(2022版) | XX证财规〔2022〕乙号 | **Explicitly Deprecated** |
| `03_authorization_management.md` | XX证券授权管理办法 | XX证综规〔2025〕丙号 | **Current / Effective** |

---

## 2. Effective Dates and Repeal Status

| Policy | Effective Date | Repeal / Deprecation |
|--------|---------------|---------------------|
| 2025 Revision (Doc 01) | 2025-01-01 | N/A (current) |
| 2022 Version (Doc 02) | (originally 2022) | **Repealed 2025-01-01** by Doc 01 Article 14 |
| Authorization Management (Doc 03) | 2025-01-01 | N/A (current) |

**Key citation — Doc 01, Article 14:**
> "本办法自二〇二五年一月一日起施行。原《XX证券费用报销管理办法(2022版)》同时废止。"

**Key citation — Doc 03, Article 5:**
> "本办法自二〇二五年一月一日起施行。"

All three documents are synchronized: the 2025 revision and the Authorization Management both took effect on January 1, 2025, and the 2022 version was simultaneously repealed on that date. There is **no transition period** — the cutover was a hard switch.

**Doc 02, Article 1 (self-description):**
> "本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。"

**Doc 02, Article 4:**
> "本办法的审批金额已被后续制度替代,不得作为现行审批依据。"

---

## 3. Full Threshold Comparison Table

### 3.1 Old (2022 Deprecated) Thresholds

The 2022 version contains only two explicit approval thresholds:

| Threshold | Amount Condition | Required Approver |
|-----------|-----------------|-------------------|
| Lower tier | < ¥8,000 | (Implicit) Department Manager |
| Article 2 | ≥ ¥8,000 | **Department General Manager** (部门总经理) |
| Article 3 | ≥ ¥30,000 | **Deputy General Manager** (分管副总) |
| Upper bound | ≥ ¥30,000+ | Deputy General Manager (no higher tier defined) |

**Citation — Doc 02, Article 2:**
> "旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。"

**Citation — Doc 02, Article 3:**
> "旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。"

### 3.2 New (2025 Current) Thresholds — Doc 03 Attachment II

| Tier | Amount Range | Required Approver(s) |
|------|-------------|---------------------|
| **AR-01** | ¥0 ≤ amount < ¥3,000 | Department Manager (部门经理) |
| **AR-02** | ¥3,000 ≤ amount < ¥10,000 | Department Manager **+ Financial Review** (部门经理,并经财务复核) |
| **AR-03** | ¥10,000 ≤ amount < ¥50,000 | Department General Manager (部门总经理) |
| **AR-04** | ¥50,000 ≤ amount < ¥200,000 | Deputy General Manager (分管副总) |
| **AR-05** | amount ≥ ¥200,000 | General Manager Office Meeting (总经理办公会) |

**Citation — Doc 03, Attachment II (approval authority table).**

### 3.3 Side-by-Side Comparison

| Amount Range (¥) | Old (2022) Approver | New (2025) Approver | **Mismatch?** |
|-------------------|--------------------|--------------------|--------------|
| [0, 3,000) | Dept. Manager | AR-01: Dept. Manager | ✅ Same |
| [3,000, 8,000) | Dept. Manager | AR-02: Dept. Manager + Financial Review | ❌ **Old misses financial review** |
| [8,000, 10,000) | **Dept. General Manager** | AR-02: Dept. Manager + Financial Review | ❌ **Old over-escalates** |
| [10,000, 30,000) | Dept. General Manager | AR-03: Dept. General Manager | ✅ Same |
| [30,000, 50,000) | **Deputy General Manager** | AR-03: Dept. General Manager | ❌ **Old over-escalates** |
| [50,000, 200,000) | Deputy General Manager | AR-04: Deputy General Manager | ✅ Same |
| [200,000, ∞) | Deputy General Manager (no higher tier) | AR-05: **GM Office Meeting** | ❌ **Old under-escalates severely** |

---

## 4. Cross-Reference Clause Analysis

### 4.1 The Delegation Chain

The 2025 revision creates a deliberate **two-level cross-reference chain**:

1. **Doc 01, Article 5** delegates threshold definition:
   > "单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。"

   This explicitly states that thresholds are **NOT** in the 2025 revision's text. Anyone reading only Doc 01 without Doc 03 has **no usable thresholds**.

2. **Doc 03, Article 2** confirms the delegation:
   > "本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。"

3. **Doc 03, Attachment II** provides the actual 5-tier table (AR-01 through AR-05).

### 4.2 Structural Implications

- The 2025 revision is **structurally different** from the 2022 version: thresholds are externalized to a separate authorization document.
- The 2022 version was **self-contained** — all thresholds were inline in Article 2 and Article 3.
- This structural change is itself a version trap: someone accustomed to the 2022 pattern of "read the reimbursement policy to find thresholds" would find the 2025 policy confusingly silent and might default to the old thresholds out of familiarity.

### 4.3 Anti-Splitting Rule (New)

**Doc 01, Article 11** introduces a new anti-splitting provision absent from the 2022 version:
> "不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。"

This means that under the new regime, even if individual amounts stay under a threshold, the **aggregate** over 7 days can trigger escalation. This was not present in the 2022 version and represents an additional dimension of misjudgment risk.

---

## 5. Specific Misjudgment Scenarios (Amount Ranges)

### Scenario A: ¥3,000 – ¥7,999 (Missing Financial Review)
- **Old rule would say:** Department Manager only (no financial review at this level)
- **New rule requires:** AR-02 → Department Manager + Financial Review
- **Risk:** Using old thresholds, a ¥5,000 expense would be approved by a department manager alone, missing the mandatory financial review. This is a compliance gap, not an over-escalation.
- **Severity:** Medium — missing control, but approver level is similar.

### Scenario B: ¥8,000 – ¥9,999 (Over-Escalation to General Manager)
- **Old rule would say:** ≥¥8,000 → Department General Manager
- **New rule requires:** AR-02 → Department Manager + Financial Review
- **Risk:** Using old thresholds, a ¥9,000 expense would be unnecessarily escalated to a Department General Manager, bypassing the financial review requirement and wasting senior management time. The old path is **wrong** — it escalates too high and skips financial review.
- **Severity:** Medium — operational inefficiency plus missing financial review.

### Scenario C: ¥10,000 – ¥29,999 (No Gap — Both Require Dept. General Manager)
- **Old rule:** Department General Manager (via ≥¥8,000 threshold)
- **New rule:** AR-03 → Department General Manager (via ≥¥10,000 threshold)
- **Risk:** Same approver role in both versions. No functional mismatch.
- **Severity:** None.

### Scenario D: ¥30,000 – ¥49,999 (Over-Escalation to Deputy General Manager)
- **Old rule would say:** ≥¥30,000 → Deputy General Manager
- **New rule requires:** AR-03 → Department General Manager
- **Risk:** Using old thresholds, a ¥40,000 expense would be escalated to a Deputy General Manager when only a Department General Manager is required. This wastes senior executive time and creates unnecessary bottlenecks.
- **Severity:** Medium-High — significant operational impact, potential delay in approval turnaround.

### Scenario E: ¥50,000 – ¥199,999 (No Gap — Both Require Deputy General Manager)
- **Old rule:** Deputy General Manager (via ≥¥30,000 threshold)
- **New rule:** AR-04 → Deputy General Manager (via ≥¥50,000 threshold)
- **Risk:** Same approver role in both versions. The threshold moved but the approver role matches.
- **Severity:** None.

### Scenario F: ≥ ¥200,000 (Missing GM Office Meeting — Most Severe)
- **Old rule would say:** Deputy General Manager (no higher tier defined)
- **New rule requires:** AR-05 → General Manager Office Meeting (总经理办公会)
- **Risk:** Using old thresholds, a ¥300,000 expense would be approved by a single Deputy General Manager, completely bypassing the mandatory General Manager Office Meeting. This is a **critical governance gap** — the old policy has no provision for amounts this large.
- **Severity:** **CRITICAL** — severe under-escalation with potential for unauthorized large expenditures.

### Scenario G: Split Claims Without Aggregate Check
- **Old rule:** No anti-splitting provision exists.
- **New rule (Article 11):** Two claims by the same employee, same expense type, within 7 days, whose total reaches a higher AR tier must be investigated.
- **Risk:** Using old rules, split claims would never be flagged. E.g., two ¥6,000 claims (total ¥12,000) within 7 days would each be treated as AR-02 (manager + review) under new rules individually, but the aggregate ¥12,000 hits AR-03 (dept. general manager) — triggering the anti-splitting investigation.
- **Severity:** High — enables systematic threshold circumvention.

---

## 6. Quantitative Summary of Gap Zones

| Gap Zone | Amount Range | Width | Old Approver | New Approver | Risk Direction |
|----------|-------------|-------|-------------|-------------|---------------|
| G1 | ¥3,000 – ¥7,999.99 | ¥5,000 | Dept. Manager | Dept. Mgr + Fin. Review | Missing control |
| G2 | ¥8,000 – ¥9,999.99 | ¥2,000 | Dept. Gen. Mgr | Dept. Mgr + Fin. Review | Over-escalation + missing review |
| G3 | ¥30,000 – ¥49,999.99 | ¥20,000 | Deputy Gen. Mgr | Dept. Gen. Mgr | Over-escalation |
| G4 | ≥ ¥200,000 | Unlimited | Deputy Gen. Mgr | GM Office Meeting | Critical under-escalation |

**Total width of gap zones with mismatched approvers:** ¥27,000 (G1+G2+G3) plus an unlimited upper tail (G4).

Note: G4 is the most dangerous because there is **no upper bound**; every amount above ¥200,000 would be severely under-escalated under the old rules.

---

## 7. Version Verification Measures

### 7.1 Technical/System Measures
1. **Expense-date-based policy routing:** Any expense with `expense_date ≥ 2025-01-01` must use Doc 01 + Doc 03 Attachment II. Any expense with `expense_date < 2025-01-01` (if not yet reimbursed) should also use current policy since the 2022 version was repealed without a grandfather clause.
2. **System configuration audit:** Verify that the reimbursement system's approval routing rules reference Doc 03 Attachment II (AR-01 through AR-05) and NOT the old thresholds (¥8,000 / ¥30,000).
3. **Hard deprecation flag:** The 2022 document (Doc 02) should be flagged as deprecated in any policy management system, with Articles 1 and 4 explicitly stating it must not be used.

### 7.2 Procedural Measures
4. **Policy cross-reference validation:** Before applying any threshold, confirm that Doc 01 Article 5 is being followed — i.e., the threshold source is Doc 03 Attachment II, not any inline text.
5. **Dual-document requirement:** No single document contains the full approval rules. The reimbursement policy (Doc 01) provides the framework; the authorization policy (Doc 03) provides the thresholds. Both must be consulted together.
6. **Anti-splitting rule awareness:** Staff must be trained on Article 11 — the old policy had no anti-splitting provision, so legacy-trained staff may not think to aggregate 7-day claims.

### 7.3 Audit Trail Measures
7. **Policy version recording:** Every approval decision should record which policy version and which Attachment II tier was applied.
8. **Cross-reference integrity check:** Automated checks should confirm that the Doc 01 → Doc 03 cross-reference is intact (e.g., Doc 03 Attachment II exists and is current).
9. **Date-of-expense vs date-of-approval validation:** Expenses dated on or after 2025-01-01 that were approved using old thresholds should be flagged as anomalies.

### 7.4 Training and Communication
10. **Staff transition training:** Ensure all approvers and finance staff understand the structural change (inline thresholds → externalized authorization tiers).
11. **Quick-reference card:** Create a one-page reference showing old vs. new thresholds to prevent muscle-memory errors.

---

## 8. Conclusion

The version trap between the 2022 and 2025 expense reimbursement policies is real and significant. The key differences are:

1. **Structural change:** Thresholds moved from inline (2022) to cross-referenced (2025 via Doc 03).
2. **Threshold shifts:** Two escalation points changed (¥8,000→¥10,000 for general manager; ¥30,000→¥50,000 for deputy general manager).
3. **New controls:** Financial review at ¥3,000 (AR-02), GM Office Meeting at ¥200,000 (AR-05), and anti-splitting (Article 11) were all absent in 2022.
4. **Most critical gap:** Amounts ≥¥200,000 have no corresponding escalation in the old rules, creating a severe governance risk.

The hard cutover on 2025-01-01 with no transition period means all expenses from that date forward must use the new thresholds. Any use of the deprecated 2022 thresholds constitutes a policy violation.

---

## 9. Citations Referenced

| Doc ID | Clause | Content |
|--------|--------|---------|
| `01_expense_reimbursement_2025.md` | Article 5 | Cross-reference to Authorization Management Attachment II |
| `01_expense_reimbursement_2025.md` | Article 11 | Anti-splitting rule |
| `01_expense_reimbursement_2025.md` | Article 14 | Effective date and repeal of 2022 version |
| `02_expense_reimbursement_2022_deprecated.md` | Article 1 | Self-declaration as deprecated archive |
| `02_expense_reimbursement_2022_deprecated.md` | Article 2 | Old ¥8,000 threshold |
| `02_expense_reimbursement_2022_deprecated.md` | Article 3 | Old ¥30,000 threshold |
| `02_expense_reimbursement_2022_deprecated.md` | Article 4 | Explicit prohibition against current use |
| `03_authorization_management.md` | Article 2 | Confirms Attachment II as current approval lines |
| `03_authorization_management.md` | Article 5 | Effective date 2025-01-01 |
| `03_authorization_management.md` | Attachment II | AR-01 through AR-05 tier table |
