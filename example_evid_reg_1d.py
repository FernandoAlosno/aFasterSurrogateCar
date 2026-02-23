import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt


# ==========================================
# 1. Dataset Generation
# ==========================================
def generate_toy_data():
    # Training data: x in [-4, 4], y = x^3 + noise
    x_train = np.random.uniform(-4, 4, 1000).astype(np.float32)
    noise = np.random.normal(0, 3, 1000).astype(np.float32)
    y_train = 40 * np.sin(x_train) + noise

    # Test data (Out of Distribution): x in [-7, 7]
    x_test = np.linspace(-7, 7, 500).astype(np.float32)
    y_test = x_test**3

    return (
        torch.tensor(x_train).unsqueeze(1),
        torch.tensor(y_train).unsqueeze(1),
        torch.tensor(x_test).unsqueeze(1),
        torch.tensor(y_test).unsqueeze(1),
    )


# ==========================================
# 2. Model Definition (Added Dropout)
# ==========================================
class EvidentialNetwork(nn.Module):
    def __init__(self, hidden_dim=64, dropout_rate=0.1):
        super(EvidentialNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),  # Added Dropout
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),  # Added Dropout
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),  # Added Dropout
            nn.Linear(hidden_dim, 4),  # Outputs: gamma, nu, alpha, beta
        )

    def forward(self, x):
        out = self.net(x)

        # Split outputs
        gamma = out[:, 0:1]  # Continuous target prediction
        nu = F.softplus(out[:, 1:2]) + 1e-6  # nu > 0
        alpha = F.softplus(out[:, 2:3]) + 1.0 + 1e-6  # alpha > 1
        beta = F.softplus(out[:, 3:4]) + 1e-6  # beta > 0

        return gamma, nu, alpha, beta


# ==========================================
# 3. Loss Function
# ==========================================
def evidential_loss(y_true, gamma, nu, alpha, beta, coeff=0.01):
    # NIG Negative Log Likelihood
    omega = 2 * beta * (1 + nu)
    nll = (
        0.5 * torch.log(np.pi / nu)
        - alpha * torch.log(omega)
        + (alpha + 0.5) * torch.log(nu * (y_true - gamma) ** 2 + omega)
        + torch.lgamma(alpha)
        - torch.lgamma(alpha + 0.5)
    )

    # Regularization: Penalize high evidence when error is high
    error = torch.abs(y_true - gamma)
    reg = error * (2 * nu + alpha)

    return torch.mean(nll + coeff * reg)


# ==========================================
# 4. Training Loop (Added Weight Decay & LR Scheduler)
# ==========================================
def train_model():
    # Hyperparameters
    epochs = 2000
    lr = 2e-3
    weight_decay = 2e-4  # L2 Regularization
    reg_coeff = 0.01

    x_train, y_train, x_test, y_test = generate_toy_data()
    model = EvidentialNetwork(dropout_rate=0.1)

    # Added Weight Decay to Optimizer
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    # Added Learning Rate Scheduler (Cosine Annealing)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print("Starting training...")
    model.train()  # Set to train mode for Dropout

    for epoch in range(epochs):
        optimizer.zero_grad()
        gamma, nu, alpha, beta = model(x_train)

        loss = evidential_loss(y_train, gamma, nu, alpha, beta, coeff=reg_coeff)
        loss.backward()

        optimizer.step()
        scheduler.step()  # Step the scheduler after optimizer

        if (epoch + 1) % 100 == 0:
            current_lr = scheduler.get_last_lr()[0]
            print(
                f"Epoch {epoch+1:4d}/{epochs} | Loss: {loss.item():.4f} | LR: {current_lr:.6f}"
            )

    return model, x_train, y_train, x_test


# ==========================================
# 5. Evaluation and Plotting
# ==========================================
def plot_results(model, x_train, y_train, x_test):
    model.eval()  # CRITICAL: Turn off Dropout for inference

    with torch.no_grad():
        gamma, nu, alpha, beta = model(x_test)

        # Calculate uncertainties
        gamma = gamma.numpy().squeeze()
        aleatoric = (beta / (alpha - 1)).numpy().squeeze()
        epistemic = (beta / (nu * (alpha - 1))).numpy().squeeze()
        total_unc = aleatoric + epistemic

        x_t = x_test.numpy().squeeze()

        # Plotting
        plt.figure(figsize=(10, 6))

        # Plot training data
        plt.scatter(
            x_train.numpy(),
            y_train.numpy(),
            color="gray",
            alpha=0.3,
            label="Train Data",
            s=10,
        )

        # Plot mean prediction
        plt.plot(x_t, gamma, "b--", label="Prediction ($\gamma$)")

        # Plot Epistemic Uncertainty (std dev)
        std_epistemic = np.sqrt(epistemic)
        plt.fill_between(
            x_t,
            gamma - 2 * std_epistemic,
            gamma + 2 * std_epistemic,
            color="red",
            alpha=0.2,
            label="Epistemic Uncertainty ($2\sigma$)",
        )

        std_aleatoric = np.sqrt(aleatoric)
        plt.fill_between(
            x_t,
            gamma - 2 * std_aleatoric,
            gamma + 2 * std_aleatoric,
            color="blue",
            alpha=0.2,
            label="Aleatoric Uncertainty ($2\sigma$)",
        )

        plt.xlim([-7, 7])
        plt.ylim([-150, 150])
        plt.title(
            "Deep Evidential Regression - With Dropout, Weight Decay, & LR Schedule"
        )
        plt.xlabel("x")
        plt.ylabel("y")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    torch.manual_seed(42)
    np.random.seed(42)

    trained_model, X_tr, Y_tr, X_te = train_model()
    plot_results(trained_model, X_tr, Y_tr, X_te)
