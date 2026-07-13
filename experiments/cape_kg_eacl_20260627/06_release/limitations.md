# Limitations

This run is an EACL experiment scaffold and silver/proxy evaluation, not a
paper-claimable final result.

- The reference labels are derived from the current AX-EPAK KG and must be
  replaced or adjudicated by two human annotators.
- Silver/proxy baseline rows remain only for metric wiring and sanity checks.
  Actual Qwen3-8B B0/B1/B2/B4/B5 generations and CAPE ablations are present,
  but paper claims still require adjudicated human-gold scoring.
- The Qwen3-8B strict JSON warning gate now passes after the top-3 warning
  conditions were rerun with a longer 2400-token strict/no-think setting; raw
  parse recovery should still be reported as an engineering reliability note.
- Qwen3-32B-AWQ has been completed for the core B0/B1/B2/P 120-chunk
  diagnostic conditions, but those scores are still silver/proxy evidence.
- Standard Qwen3-32B full-precision/standard-weight execution is not currently
  recommended on this disk state; free additional space before attempting it.
- PAGED/Text2KGBench public subset runs are diagnostic small-subset checks, not
  full public benchmark leaderboard results.
- Raw text release still requires copyright review.
