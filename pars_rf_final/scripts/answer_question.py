"""Run the final method on an explicitly supplied graph snapshot and question.

Live embedding/generation requires --allow-api and OPENAI_API_KEY. The original
document corpus and graph snapshot are not distributed with this release.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "runs/live")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--allow-api", action="store_true")
    args = parser.parse_args()
    if not args.allow_api:
        parser.error("Live calls are disabled; use --allow-api or scripts/replay_example.py")
    if not args.snapshot.is_file():
        parser.error("Snapshot file does not exist")
    if not args.question.strip():
        parser.error("Question must not be empty")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        parser.error("OPENAI_API_KEY is not set")

    from kg_rag.cover_api import CoverAPI, CoverAPIError
    from kg_rag.cover_cache import CoverEmbeddingBackend
    from kg_rag.cover_index import build_cover_index
    from kg_rag.cover_retrieval import EmbeddedCoverIndex
    from kg_rag.cover_runtime import CoverRuntime
    from kg_rag.adaptive_runtime import AdaptiveRuntime
    from kg_rag.retrieval import GraphIndex
    from kg_rag.reranking import CrossEncoderReranker
    from kg_rag.refined_runtime import retrieve_refined
    from kg_rag.shared_context import validate_local_citations
    from kg_rag.common import utc_now

    config = json.loads((ROOT / "config/final_method.json").read_text())
    final = config["final_method"]
    assert final == {"method": "PARS_REFINED", "variant": "CE_TOP5", "question_top_k": 40,
                     "aspect_top_k": 20, "evidence_top_k": 5, "aspect_limit": None,
                     "context_budget_chars": 7000}, "Do not silently change the final contract"
    snapshot = json.loads(args.snapshot.read_text())
    raw = build_cover_index(snapshot)
    rules = json.loads((ROOT / "config/aspect_rules.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)

    def event(record):
        with (args.output / "api_usage.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"time": utc_now(), **record}, ensure_ascii=False) + "\n")

    api = CoverAPI(key, config, on_event=event)
    del key
    backend = CoverEmbeddingBackend(api, args.output / "embeddings.sqlite")
    try:
        graph = GraphIndex(snapshot, backend, embedding_batch_size=128)
        texts = list(dict.fromkeys(v.text for v in raw.views))
        vectors = dict(zip(texts, backend.embed_exact(texts, batch_size=128)))
        embedded = EmbeddedCoverIndex.prepare(raw, {v.view_id: vectors[v.text] for v in raw.views})
        # CoverRuntime preserves historical internals. CE_TOP5 fixes final selection.
        legacy = {"pcf_grounded_aspect": {"selected_k": 3}}
        runtime = AdaptiveRuntime(CoverRuntime(graph, embedded, backend, config, legacy, rules, 7000), rules)
        reranker = CrossEncoderReranker({"model": config["models"]["legacy_reranker"],
                                       "revision": config["models"]["legacy_reranker_revision"],
                                       "device": args.device, "batch_size": 32, "max_length": 512})
        retrieved = retrieve_refined(runtime, reranker, args.question, "CE_TOP5")
        user = f"[QUESTION]\n{args.question}\n\n[RETRIEVAL CONTEXT]\n{retrieved['context']}"

        def generate(kind, content):
            prompt = (ROOT / config["generation"][kind + "_prompt"]).read_text()
            schema = json.loads((ROOT / config["generation"][kind + "_schema"]).read_text())
            return api.structured(kind, prompt, schema, content, retrieved["citation_map"])

        draft = generate("answer", user)
        verified = generate("verifier", user + "\n\n[DRAFT]\n" + json.dumps(draft, ensure_ascii=False))
        ids = validate_local_citations(verified["supported_citations"], retrieved["citation_map"])
        result = {"method": "PARS_REFINED", "question": args.question,
                  "status": "ANSWERED" if draft["status"] == "ANSWERED" and verified["supported"] and ids else "INSUFFICIENT",
                  "answer": verified["corrected_answer"], "citations": verified["supported_citations"],
                  "draft": draft, "verification": verified, "retrieval": retrieved}
        (args.output / "answer.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ["status", "answer", "citations"]}, ensure_ascii=False, indent=2))
    except CoverAPIError as exc:
        print(json.dumps({"api_error": exc.record()}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        backend.db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
