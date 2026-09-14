"""Linear Router 정의 및 공통 학습/valid 선택/최종 test 평가."""

import argparse
import copy
import json
from pathlib import Path
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from generate_vectors import FEATURE_NAMES, ROOT, sha256, write_json, write_jsonl


class LinearRouter(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer = nn.Linear(3, 1)

    def forward(self, features):
        return self.layer(features).squeeze(-1)  # logits. Sigmoid는 loss/예측에서 적용.


def router_loss(logits, labels, loss_name, pos_weight, mix_lambda, beta):
    # y=1: 검색 필요. Weighted BCE = -[w*y*log(p)+(1-y)*log(1-p)].
    # pos_weight=w를 키우면 필요한 검색을 생략한 오류(FN)에 더 큰 비용을 준다.
    # BCEWithLogitsLoss는 sigmoid와 BCE를 함께 계산해 수치적으로 안정적이다.
    bce = nn.functional.binary_cross_entropy_with_logits(logits, labels, pos_weight=logits.new_tensor(pos_weight))
    if loss_name == "weighted_bce":
        return bce
    # PDF의 F-beta 기반 손실: 이산 F-beta는 미분 불가능하므로 확률 기반 근사 사용.
    # soft TP=sum(p*y), FP=sum(p*(1-y)), FN=sum((1-p)*y).
    # beta=2이면 Recall을 강조한다. F-beta를 최대화해야 하므로 loss=1-soft_F_beta.
    probabilities = logits.sigmoid()
    tp = (probabilities * labels).sum()
    fp = (probabilities * (1 - labels)).sum()
    fn = ((1 - probabilities) * labels).sum()
    soft_fbeta = (1 + beta**2) * tp / ((1 + beta**2) * tp + beta**2 * fn + fp + 1e-8)
    # 최종 loss = lambda * weighted_BCE + (1-lambda) * (1-soft_F_beta).
    return mix_lambda * bce + (1 - mix_lambda) * (1 - soft_fbeta)


def metrics(labels, probabilities, threshold, beta=2.0):
    y = np.asarray(labels).astype(bool)
    pred = np.asarray(probabilities) >= threshold
    tp, fp = int((y & pred).sum()), int((~y & pred).sum())
    fn, tn = int((y & ~pred).sum()), int((~y & ~pred).sum())
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    denominator = (1 + beta**2) * tp + beta**2 * fn + fp
    return {"count": len(y), "positive_count": int(y.sum()), "negative_count": int((~y).sum()),
            "single_class": len(np.unique(y)) < 2, "threshold": float(threshold),
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "precision": precision, "recall": recall,
            "fbeta": float((1 + beta**2) * tp / denominator) if denominator else None,
            "beta": beta, "false_positive_rate": fp / (fp + tn) if fp + tn else None,
            "search_rate": float(pred.mean()), "accuracy": (tp + tn) / len(y)}


def choose_threshold(labels, probabilities, target_recall):
    # 한 클래스 valid에서 Recall을 맞추면 '항상 검색'만 선택하므로 최적화하지 않는다.
    if len(np.unique(labels)) < 2:
        return 0.5, "single_class_valid: fixed_0.5; threshold_not_tuned"
    candidates = np.unique(np.r_[0.0, 0.5, probabilities, 1.0])
    feasible = []
    for threshold in candidates:
        result = metrics(labels, probabilities, threshold)
        if result["recall"] >= target_recall:
            feasible.append((result["false_positive_rate"], result["search_rate"], -float(threshold)))
    best = min(feasible)
    return -best[2], f"valid_only: minimize_false_positive_rate_at_recall>={target_recall}"


def train_main(model_factory=LinearRouter, model_type="linear"):
    parser = argparse.ArgumentParser(description=f"{model_type.upper()} Router 학습 및 검증")
    parser.add_argument("--vectors-dir", type=Path, default=ROOT / "artifacts/bge_m3")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--loss", choices=["weighted_bce", "weighted_bce_fbeta"], default="weighted_bce")
    parser.add_argument("--pos-weight", type=float, default=2.0)
    parser.add_argument("--mix-lambda", type=float, default=0.8)
    parser.add_argument("--beta", type=float, default=2.0)
    parser.add_argument("--target-recall", type=float, default=0.95)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if min(args.epochs, args.patience, args.batch_size, args.lr, args.pos_weight, args.beta) <= 0 or args.weight_decay < 0:
        parser.error("학습 인자는 양수이고 weight-decay는 0 이상이어야 합니다.")
    if not 0 <= args.mix_lambda <= 1 or not 0 < args.target_recall <= 1:
        parser.error("mix-lambda는 [0,1], target-recall은 (0,1]이어야 합니다.")
    vectors_dir = args.vectors_dir.resolve()
    out = (args.output_dir or vectors_dir / model_type).resolve()
    if (out / "model.pt").exists():
        parser.error("체크포인트가 이미 있습니다. 새 --output-dir를 사용하세요.")
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((vectors_dir / "manifest.json").read_text())
    if manifest["feature_names"] != FEATURE_NAMES or sha256(vectors_dir / "vectors.npz") != manifest["vectors_sha256"]:
        raise ValueError("벡터 파일 또는 특징 순서가 manifest와 다릅니다.")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)
    with np.load(vectors_dir / "vectors.npz", allow_pickle=False) as data:
        x, y, splits, qa_ids = (data[k].copy() for k in ("features", "labels", "splits", "qa_ids"))
    if x.shape != (len(y), 3) or not np.isfinite(x).all() or not set(np.unique(y)).issubset({0, 1}):
        raise ValueError("잘못된 벡터/라벨입니다.")
    masks = {s: splits == s for s in ("train", "valid", "test")}
    if not all(mask.any() for mask in masks.values()):
        raise ValueError("train/valid/test가 모두 있어야 합니다.")
    # 정규화 통계는 train에서만 추정한다. valid/test 정보는 학습에 쓰지 않는다.
    mean, std = x[masks["train"]].mean(axis=0), x[masks["train"]].std(axis=0)
    std = np.maximum(std, 1e-6)
    tensors = {s: (torch.from_numpy((x[m] - mean) / std), torch.from_numpy(y[m])) for s, m in masks.items()}
    loader = DataLoader(TensorDataset(*tensors["train"]), batch_size=args.batch_size, shuffle=True,
                        generator=torch.Generator().manual_seed(args.seed))
    model = model_factory()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    best_loss, best_state, best_epoch, stale = float("inf"), None, 0, 0
    history = []
    single_class = len(np.unique(y[masks["train"]])) < 2
    if single_class:
        print("주의: train이 한 클래스입니다. 실행 확인용이며 검색 불필요 판별 능력은 학습/검증되지 않습니다.", flush=True)

    def loss_fn(logits, labels):
        return router_loss(logits, labels, args.loss, args.pos_weight, args.mix_lambda, args.beta)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(batch_x), batch_y)
            if not torch.isfinite(loss):
                raise ValueError("학습 loss가 유한하지 않습니다.")
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(batch_y)
        model.eval()
        with torch.no_grad():
            valid_loss = loss_fn(model(tensors["valid"][0]), tensors["valid"][1]).item()
        history.append({"epoch": epoch, "train_loss": total_loss / int(masks["train"].sum()), "valid_loss": valid_loss})
        if valid_loss < best_loss - 1e-6:
            best_loss, best_state, best_epoch, stale = valid_loss, copy.deepcopy(model.state_dict()), epoch, 0
        else:
            stale += 1
        if epoch == 1 or epoch % 25 == 0:
            print(f"epoch={epoch} train_loss={history[-1]['train_loss']:.6f} valid_loss={valid_loss:.6f}", flush=True)
        if stale >= args.patience:
            break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        valid_p = model(tensors["valid"][0]).sigmoid().numpy()
    threshold, threshold_note = choose_threshold(y[masks["valid"]], valid_p, args.target_recall)
    report = {"model_type": model_type, "single_class_training": single_class, "best_epoch": best_epoch,
              "loss": {"name": args.loss, "pos_weight": args.pos_weight, "lambda": args.mix_lambda, "beta": args.beta},
              "threshold_selection": threshold_note, "splits": {}}
    # 모델/임계값 선택이 모두 끝난 뒤에만 test 예측을 생성한다.
    for split, mask in masks.items():
        with torch.no_grad():
            p = model(tensors[split][0]).sigmoid().numpy()
        report["splits"][split] = metrics(y[mask], p, threshold, args.beta)
        report["splits"][split]["always_search"] = metrics(y[mask], np.ones_like(p), 0.5, args.beta)
        report["splits"][split]["never_search"] = metrics(y[mask], np.zeros_like(p), 0.5, args.beta)
        write_jsonl(out / f"{split}_predictions.jsonl", [{"qa_id": str(q), "label": int(label),
                     "search_score": float(score), "needs_search": bool(score >= threshold)}
                     for q, label, score in zip(qa_ids[mask], y[mask], p)])
    checkpoint = {"model_type": model_type, "state_dict": best_state, "feature_mean": torch.from_numpy(mean),
                  "feature_std": torch.from_numpy(std), "threshold": threshold,
                  "vectors_dir": str(vectors_dir), "vectors_sha256": manifest["vectors_sha256"],
                  "manifest_sha256": sha256(vectors_dir / "manifest.json"), "single_class_training": single_class,
                  "seed": args.seed, "best_epoch": best_epoch}
    torch.save(checkpoint, out / "model.pt")
    write_json(out / "metrics.json", report)
    write_json(out / "training_config.json", {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()})
    write_jsonl(out / "history.jsonl", history)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print(f"저장: {out / 'model.pt'}", flush=True)


if __name__ == "__main__":
    train_main()
