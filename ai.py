import torch.nn as nn

class TDGammonNetwork(nn.Module):
    def __init__(self):
        super(TDGammonNetwork, self).__init__()
        self.hidden = nn.Sequential(
            nn.Linear(198, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.hidden(x)