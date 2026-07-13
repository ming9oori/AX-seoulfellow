# Candidate Lattice v1 Report

## Static validation

| Dataset | Evidence | Candidates | Median | p95 | Max | Offset | IDs | Structure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DEV_EXPOSED | 60 | 213 | 2.0 | 13.0 | 24 | 1.00 | 1.00 | 1.00 |
| MODEL_BAKEOFF | 24 | 66 | 3.0 | 6.0 | 8 | 1.00 | 1.00 | 1.00 |
| R2_PILOT | 60 | 117 | 1.0 | 8.1 | 13 | 1.00 | 1.00 | 1.00 |

The program generated every quote from `raw_text[start_char:end_char]`. No LLM generated a quote or offset.

R0 `missing_candidate_rate` was not measured on fresh R2_PILOT because the model panel could not be locked. Static R0 constraints passed; the full R0 Gate remains `NOT_EVALUATED`.
