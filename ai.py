import torch.nn as nn

class TGGammonNetwork(nn.Module):
    def __init__(self):
        super(TGGammonNetwork, self).__init__()
        self.hidden = nn.Sequential(
            nn.Linear(198, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.hidden(x)