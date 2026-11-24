# SEED baseline security audit

| Severity | Finding | P1 disposition |
| --- | --- | --- |
| High | Closer approval previews the first body only, recommends connector delivery, and hashes the EML independently of its target thread. | Review all exact payloads, bind thread metadata, keep remote writes outside the P1 agent workflows. |
| High | Closer accepts a workspace-relative draft path from its pipeline, with no containment check. Data-room enumeration can recommend linked files and its index can overwrite a linked path. | Constrain managed paths, use atomic replacement, add negative regressions. |
| High | Public materials and private venture data can share a checkout with no ignore rules. | Use a separate private working directory, ignore common generated paths and package from a fixed allowlist. |
| Medium | Retrieved text and mail are untrusted, and source URLs provide no claim-level verification by themselves. | Add a trust boundary to the portable instructions. Evidence verification and freshness move into the P2 data model. |
| Medium | Filename-based diligence and numeric token matches do not verify file sensitivity or prove assertion consistency. | Treat results as candidates for human review. Carry semantic claims and explicit disclosure levels into later phases. |
| Medium | Legacy tools assume a trusted private directory and single writer. Several writers use predictable temporary names or non-atomic updates. | Harden Closer and the data-room index in P1. Add transactional records in P2 before shared concurrent access. |
