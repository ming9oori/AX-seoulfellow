"""MLP Router(3→16→1) 정의 및 학습/검증. 학습 절차는 Linear와 동일."""

from torch import nn

from train_linear import train_main


class MLPRouter(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(3, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, features):
        return self.layers(features).squeeze(-1)


if __name__ == "__main__":
    train_main(MLPRouter, "mlp")
