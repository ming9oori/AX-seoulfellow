"""온톨로지 추출, 기존 QA 분할, Encoder 벡터 및 PDF의 3개 유사도 생성."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import torch
import numpy as np

ROOT = Path(__file__).resolve().parent
TYPES = ("TaskFrame", "TaskMention", "Relation")
FEATURE_NAMES = [f"{kind}_max_cosine" for kind in TYPES]
BEHAVIOR_LABELS = {"answer_with_evidence": 1, "answer_directly": 0}


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_ontology(path):
    """현재 저장된 v4 HTML의 전용 영역만 읽어 중복 표시를 제거한다."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    records = {}

    def text(element):
        return element.get_text(" ", strip=True) if element else ""

    for frame in soup.select("#frame-list > article.frame-card"):
        frame_id = frame["id"].removeprefix("frame-")
        header = frame.select_one(".frame-header")
        aliases = text(frame.select_one(".aliases")).removeprefix("Aliases").strip(" ·")
        parts = [text(header.select_one("h3")), text(header.select_one("p")),
                text(frame.select_one(".frame-meta .badge.scope")), aliases]
        records[frame_id] = {"id": frame_id, "type": "TaskFrame", "text": "\n".join(p for p in parts if p)}
        for mention in frame.select("article.mention-card"):
            mention_id = text(mention.select_one(".mono"))
            if not mention_id:
                raise ValueError("TaskMention ID가 없는 HTML 항목입니다.")
            parts = [text(mention.select_one(".row-between strong")), text(mention.select_one(".mention-signature"))]
            records[mention_id] = {"id": mention_id, "type": "TaskMention", "text": "\n".join(p for p in parts if p),
                                "taskframe_id": frame_id}

    # Relation은 그래프 edge 이름이 아니라 Fact의 원문 predicate이다.
    # 정규화 미확정 상태에서 의미가 다른 관계를 임의로 병합하지 않는다.
    fact_count = 0
    for fact in soup.select("#fact-table tbody > tr[id^='fact-']"):
        predicate = text(fact.select_one(".predicate"))
        if not predicate:
            raise ValueError(f"Relation 표현이 없는 Fact: {fact['id']}")
        fact_count += 1
        relation_id = "RE_" + hashlib.sha256(predicate.encode()).hexdigest()[:16]
        if relation_id not in records:
            records[relation_id] = {"id": relation_id, "type": "Relation", "text": predicate, "fact_ids": []}
        records[relation_id]["fact_ids"].append(fact["id"].removeprefix("fact-"))
    counts = Counter(row["type"] for row in records.values())
    if any(counts[kind] == 0 for kind in TYPES):
        raise ValueError(f"HTML에서 세 유형을 모두 추출하지 못했습니다: {dict(counts)}")
    return list(records.values()), fact_count


def routing_label(row, label_column=None):
    """answerable/ontology_answerable은 검색 필요 여부와 다르므로 사용하지 않는다."""
    column = label_column or "needs_search"
    value = row.get(column)
    if value is not None and value != "":
        if value in (True, 1, "1", "true"):
            return 1, column
        if value in (False, 0, "0", "false"):
            return 0, column
        raise ValueError(f"{row.get('qa_id')}: {column}은 0/1이어야 합니다: {value!r}")
    if label_column:
        raise ValueError(f"{row.get('qa_id')}: {label_column} 라벨이 없습니다.")
    behavior = row.get("expected_behavior")
    if behavior not in BEHAVIOR_LABELS:
        raise ValueError(f"{row.get('qa_id')}: 알 수 없는 expected_behavior={behavior!r}. needs_search 또는 --label-column을 지정하세요.")
    return BEHAVIOR_LABELS[behavior], "expected_behavior"


def split_qa(rows, seed, ratios, label_column=None):
    """같은 절/원문 행/동일 질문은 하나의 연결 그룹으로 묶어 분리한다."""
    from sklearn.model_selection import GroupShuffleSplit

    if len(rows) < 3 or len({r.get("qa_id") for r in rows}) != len(rows):
        raise ValueError("QA는 3개 이상이어야 하며 qa_id는 고유해야 합니다.")
    if any(not r.get("qa_id") or not str(r.get("question", "")).strip() for r in rows):
        raise ValueError("모든 QA에는 qa_id와 question이 필요합니다.")
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owners = {}
    for i, row in enumerate(rows):
        source = (str(row.get("source_file", "")), str(row.get("sheet_name", "")))
        section = row.get("section_no")
        if section is None or section == "":
            raise ValueError(f"{row['qa_id']}: 절 단위 분리에 필요한 section_no가 없습니다.")
        keys = [("section", *source, str(row.get("chapter_no", "")), str(section)),
                ("question", " ".join(row["question"].split()).casefold())]
        keys += [("source_row", *source, str(r)) for r in (row.get("source_row_ids") or [])]
        for key in keys:
            if key in owners:
                parent[find(i)] = find(owners[key])
            else:
                owners[key] = i
                
    groups = np.array([find(i) for i in range(len(rows))])
    if len(set(groups)) < 3:
        raise ValueError("서로 독립인 원문 그룹이 3개 미만이어서 train/valid/test를 나눌 수 없습니다.")
    
    indices = np.arange(len(rows))
    train, rest = next(GroupShuffleSplit(n_splits=1, train_size=ratios[0], random_state=seed).split(indices, groups=groups))
    
    if len(set(groups[rest])) < 2:
        raise ValueError("valid/test용 그룹이 부족합니다. --ratios를 조정하세요.")
    
    valid_local, test_local = next(GroupShuffleSplit(n_splits=1, train_size=ratios[1] / sum(ratios[1:]), random_state=seed).split(rest, groups=groups[rest]))
    assignments = {}
    
    for name, ids in (("train", train), ("valid", rest[valid_local]), ("test", rest[test_local])):
        assignments.update({int(i): name for i in ids})
        
        
    prepared = []
    for i, row in enumerate(rows):
        label, label_source = routing_label(row, label_column)
        prepared.append({
            **row, "split": assignments[i], 
            "needs_search": label,
            "router_label_source": label_source, 
            "router_group": f"group_{groups[i]:04d}"
            })
    return prepared


def load_encoder(config, device=None):
    """SentenceTransformer 호환 모델 ID 또는 로컬 모델 경로를 받는다."""
    cache_dir = Path(config["cache_dir"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_dir))
    from sentence_transformers import SentenceTransformer

    encoder = SentenceTransformer(config["model_name"], revision=config.get("revision"),
                                cache_folder=str(cache_dir), device=device)
    encoder.max_seq_length = config["max_length"]
    return encoder


def encode(encoder, texts, prefix, batch_size, progress=False):
    return encoder.encode([prefix + t for t in texts], batch_size=batch_size, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=progress).astype(np.float32)


def similarity_features(query_vectors, ontology_vectors):
    """PDF 그대로 유형별 최대 코사인 유사도 3개만 반환한다."""
    return np.column_stack([(query_vectors @ ontology_vectors[kind].T).max(axis=1) for kind in TYPES]).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa", type=Path, default=ROOT.parent / "jaije_qa_dataset/qa_dataset.jsonl")
    parser.add_argument("--ontology-html", type=Path, default=ROOT.parent / "code_hyuna/taskframe_v4/final_report/task_centric_open_kg_report_v2.html")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/bge_m3")
    parser.add_argument("--model-name", default="BAAI/bge-m3")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "artifacts/model_cache")
    parser.add_argument("--query-prefix", default="")
    parser.add_argument("--ontology-prefix", default="")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ratios", type=float, nargs=3, default=[0.7, 0.15, 0.15], metavar=("TRAIN", "VALID", "TEST"))
    parser.add_argument("--label-column", help="0/1 검색 필요 라벨 컬럼. 미지정 시 needs_search 또는 expected_behavior 사용")
    parser.add_argument("--prepare-only", action="store_true", help="Encoder 로딩 없이 데이터 추출과 분할만 실행")
    args = parser.parse_args()
    
    
    if any(r <= 0 for r in args.ratios) or not np.isclose(sum(args.ratios), 1):
        parser.error("--ratios는 양수 3개이며 합이 1이어야 합니다.")
    
    if min(args.max_length, args.batch_size, args.threads) < 1:
        parser.error("max-length, batch-size, threads는 양수여야 합니다.")
        
    out = args.output_dir.resolve()
    # 다른 Encoder의 벡터/체크포인트가 섞이는 것을 막는다. 재실행은 새 디렉터리 사용.
    
    if (out / "manifest.json").exists():
        parser.error("완료된 벡터가 있습니다. 새 --output-dir를 사용하세요.")
    out.mkdir(parents=True, exist_ok=True)
    
    ontology, fact_count = extract_ontology(args.ontology_html)
    rows = split_qa(read_jsonl(args.qa), args.seed, args.ratios, args.label_column)
    
    
    write_jsonl(out / "ontology.jsonl", ontology)
    for split in ("train", "valid", "test"):
        write_jsonl(out / f"{split}.jsonl", [r for r in rows if r["split"] == split])
        
        
    summary = {
        "seed": args.seed, 
        "requested_ratios": args.ratios,
        "source_qa": str(args.qa.resolve()), 
        "source_qa_sha256": sha256(args.qa),
        "source_ontology": str(args.ontology_html.resolve()), 
        "source_ontology_sha256": sha256(args.ontology_html),
        "ontology_counts": dict(Counter(r["type"] for r in ontology)), 
        "source_fact_count": fact_count,
        "splits": {
            s: {
                "count": sum(r["split"] == s for r in rows),
                "groups": len({r["router_group"] for r in rows if r["split"] == s}),
                "labels": dict(Counter(str(r["needs_search"]) for r in rows if r["split"] == s))
                }
            for s in ("train", "valid", "test")
        },
        "single_class_pilot": len({r["needs_search"] for r in rows}) < 2}
    
    
    write_json(out / "data_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    
    
    if summary["single_class_pilot"]:
        print("주의: 현재는 한 클래스 파일럿입니다. 이진 분류 성능을 검증할 수 없습니다.", flush=True)
    if args.prepare_only:
        return
    
    
    torch.set_num_threads(args.threads)
    config = {
        "model_name": args.model_name, 
        "revision": args.revision, 
        "cache_dir": str(args.cache_dir.resolve()),
        "max_length": args.max_length, 
        "query_prefix": args.query_prefix, 
        "ontology_prefix": args.ontology_prefix
        }
    encoder = load_encoder(config, args.device)
    
    
    # 다운로드된 모델의 실제 commit을 저장해 실행 시 동일한 Encoder를 사용한다.
    model_config = getattr(getattr(encoder[0], "auto_model", None), "config", None)
    config["revision"] = getattr(model_config, "_commit_hash", None) or args.revision
    
    
    ontology_vectors = {}
    for kind in TYPES:
        texts = [r["text"] for r in ontology if r["type"] == kind]
        ontology_vectors[kind] = encode(encoder, texts, args.ontology_prefix, args.batch_size, True)
        
    
    queries = encode(encoder, [r["question"] for r in rows], args.query_prefix, args.batch_size, True)
    features = similarity_features(queries, ontology_vectors)
    
    
    if not np.isfinite(features).all():
        raise ValueError("유사도에 NaN/Inf가 있습니다.")
    
    
    np.savez_compressed(
        out / "vectors.npz", **ontology_vectors, query_vectors=queries, features=features,
        labels=np.array([r["needs_search"] for r in rows], dtype=np.float32),
        splits=np.array([r["split"] for r in rows]), qa_ids=np.array([r["qa_id"] for r in rows])
    )
    
    
    manifest = {
        "encoder": config, "feature_names": FEATURE_NAMES, "dimension": int(queries.shape[1]),
        "data_summary": summary, "vectors_sha256": sha256(out / "vectors.npz"),
        "ontology_sha256": sha256(out / "ontology.jsonl")
    }
    
    write_json(out / "manifest.json", manifest)
    print(f"벡터 생성 완료: {out}", flush=True)


if __name__ == "__main__":
    main()
