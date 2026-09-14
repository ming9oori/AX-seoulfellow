"""저장된 Linear Router와 동일 Encoder/온톨로지로 새 질문의 검색 여부 예측."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from generate_vectors import ROOT, TYPES, FEATURE_NAMES, encode, load_encoder, sha256, similarity_features
from train_linear import LinearRouter


def run_main(model_factory=LinearRouter, model_type="linear"):
    parser = argparse.ArgumentParser(description=f"저장된 {model_type.upper()} Router 실행")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / f"artifacts/bge_m3/{model_type}/model.pt")
    parser.add_argument("--vectors-dir", type=Path, help="벡터 폴더를 이동한 경우 지정; 학습 시 해시와 일치해야 함")
    parser.add_argument("--cache-dir", type=Path, help="Encoder 다운로드 캐시 경로 변경")
    parser.add_argument("--query", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    
    
    if not args.query.strip() or args.threads < 1:
        parser.error("query는 비어 있을 수 없으며 threads는 양수여야 합니다.")
    torch.set_num_threads(args.threads)
    
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if checkpoint["model_type"] != model_type:
        parser.error(f"{checkpoint['model_type']} 체크포인트입니다. 해당 run 파일을 사용하세요.")
    vectors_dir = args.vectors_dir or Path(checkpoint["vectors_dir"])
    
    
    if sha256(vectors_dir / "manifest.json") != checkpoint["manifest_sha256"]:
        raise ValueError("학습 때 사용한 manifest와 다릅니다.")
    
    if sha256(vectors_dir / "vectors.npz") != checkpoint["vectors_sha256"]:
        raise ValueError("학습 때 사용한 온톨로지 벡터와 다릅니다.")
    
    
    manifest = json.loads((vectors_dir / "manifest.json").read_text())
    config = dict(manifest["encoder"])
    
    if args.cache_dir:
        config["cache_dir"] = str(args.cache_dir.resolve())
        
    encoder = load_encoder(config, args.device)
    query_vector = encode(encoder, [args.query], config["query_prefix"], 1)
    
    
    with np.load(vectors_dir / "vectors.npz", allow_pickle=False) as data:
        features = similarity_features(query_vector, {kind: data[kind] for kind in TYPES})
        
    normalized = (torch.from_numpy(features) - checkpoint["feature_mean"]) / checkpoint["feature_std"]
    model = model_factory()
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    
    with torch.no_grad():
        score = model(normalized).sigmoid().item()
        
    result = {"query": args.query, "model_type": model_type, "needs_search": score >= checkpoint["threshold"],
            "search_score": score, "threshold": checkpoint["threshold"],
            "similarities": dict(zip(FEATURE_NAMES, features[0].tolist())),
            "single_class_pilot": checkpoint["single_class_training"]}
    
    if checkpoint["single_class_training"]:
        result["note"] = "파일럿 테스트 결과임."
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    run_main()
