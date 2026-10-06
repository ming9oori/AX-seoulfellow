"""Reject unknown keys and silent changes to the preregistered v1 constants."""
from __future__ import annotations


def validate_config(config):
    keys = {
        "": "contract_version experiment_name asset_origin legacy_config legacy_run spec dataset_450_enabled models retrieval context generation evaluation benchmark",
        "models": "embedding_provider embedding embedding_dimensions answer_generator legacy_reranker legacy_reranker_revision bertscore bertscore_revision",
        "retrieval": "methods pcf_top_k taskframe_top_k evidence_top_k legacy_gap_policy cover_gap_policy beta lambda lexical_weight semantic_weight aspect_rule_version template_version embedding_batch_size embedding_max_input_tokens embedding_max_batch_tokens",
        "context": "mode base_chars budget_rounding_chars safety_limit_chars truncate",
        "generation": "endpoint temperature top_p max_output_tokens concurrency max_retries sdk_max_retries store fail_on_api_error answer_prompt verifier_prompt answer_schema verifier_schema",
        "evaluation": "split_source bootstrap_iterations bootstrap_seed retrieval_primary retrieval_secondary answer_bootstrap_unit bertscore_layers bertscore_idf bertscore_rescale_with_baseline",
        "benchmark": "warmup_questions repeats concurrency final_result_cache",
    }
    for section, names in keys.items():
        value = config[section] if section else config
        if not isinstance(value, dict) or set(value) != set(names.split()):
            raise ValueError(f"Unknown or missing config keys: {section or 'root'}")
    fixed = {
        "dataset_450_enabled": False,
        "models.embedding_provider": "openai", "models.embedding": "text-embedding-3-small",
        "models.embedding_dimensions": 1536, "models.answer_generator": "gpt-4o-mini-2024-07-18",
        "models.legacy_reranker_revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
        "models.bertscore_revision": "c23d21b0620b635a76227c604d44e43a9f0ee389",
        "retrieval.methods": ["LEGACY_PARS", "PARS_COVER", "PARS_COVER_NO_SET", "PARS_COVER_TEXT_ONLY"],
        "retrieval.pcf_top_k": 3, "retrieval.taskframe_top_k": 3, "retrieval.evidence_top_k": 5,
        "retrieval.legacy_gap_policy": "legacy_union_top3", "retrieval.cover_gap_policy": "spec_fill_missing",
        "retrieval.beta": .1, "retrieval.lambda": .5, "retrieval.lexical_weight": .25, "retrieval.semantic_weight": .75,
        "retrieval.embedding_max_input_tokens": 8192, "retrieval.embedding_max_batch_tokens": 300000,
        "context.mode": "shared_evidence_only", "context.base_chars": 6000,
        "context.budget_rounding_chars": 1000, "context.safety_limit_chars": 32000, "context.truncate": False,
        "generation.endpoint": "responses", "generation.temperature": 0, "generation.top_p": 1,
        "generation.max_output_tokens": 350, "generation.concurrency": 8, "generation.max_retries": 5,
        "generation.sdk_max_retries": 0, "generation.store": False, "generation.fail_on_api_error": True,
        "evaluation.bootstrap_iterations": 10000, "evaluation.bootstrap_seed": 20260930,
        "evaluation.retrieval_primary": "Complete@5", "evaluation.retrieval_secondary": "Recall@5",
        "evaluation.answer_bootstrap_unit": "document_section", "evaluation.bertscore_layers": 17,
        "evaluation.bertscore_idf": False, "evaluation.bertscore_rescale_with_baseline": False,
        "benchmark.warmup_questions": 3, "benchmark.repeats": 5,
        "benchmark.concurrency": 1, "benchmark.final_result_cache": False,
    }
    for path, expected in fixed.items():
        value = config
        for key in path.split("."):
            value = value[key]
        if value != expected or isinstance(expected, bool) and type(value) is not bool:
            raise ValueError(f"Frozen v1 value changed: {path}")
    return config
