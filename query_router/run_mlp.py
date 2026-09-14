"""저장된 MLP Router를 불러와 새 질문의 검색 여부 예측."""

# 파일 수를 줄이기 위해 CLI/Encoder/벡터 로딩 절차만 공유한다.
# 이 import 자체는 Linear 모델이나 체크포인트를 불러오지 않는다.
from run_linear import run_main as run_router
from train_mlp import MLPRouter


if __name__ == "__main__":
    # MLPRouter를 생성하고 기본적으로 artifacts/bge_m3/mlp/model.pt를 로드한다.
    run_router(model_factory=MLPRouter, model_type="mlp")
