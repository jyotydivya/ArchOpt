"""
ml/training/train.py
====================
Train the campus GNN on synthetic graphs with the self-supervised losses in
ml/training/loss.py, then write the checkpoint used by generate_candidates().

Usage (from repo root, needs PyTorch):
    python -m ml.training.train
    python -m ml.training.train --steps 500 --out /tmp/campus_model.npz
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from ml.models.campus_model import DEFAULT_WEIGHTS_PATH, TORCH_AVAILABLE, ModelConfig, save_params
from ml.models.features import prepare_graph
from ml.training.mock_graph import build_mock_campus_graph, random_campus_graph


def train(
    steps: int = 3000,
    graphs_per_step: int = 4,
    samples_per_graph: int = 8,
    lr: float = 3e-3,
    seed: int = 0,
    min_gap: float = 10.0,
    mock_graph_prob: float = 0.25,
    out_path: Union[str, Path, None] = DEFAULT_WEIGHTS_PATH,
    log_every: int = 250,
    weights: Optional["LossWeights"] = None,
) -> Dict[str, float]:
    """
    Train from scratch and save the weights to `out_path` (skip saving if None).

    Each step averages the loss over `graphs_per_step` graphs — mostly random
    synthetic campuses, sometimes the MVP mock campus — with
    `samples_per_graph` latent samples each. Returns the mean loss parts over
    the final logging window.
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("Training needs PyTorch: pip install torch")

    import torch

    from ml.models.campus_model import CampusModel
    from ml.training.loss import LossWeights, graph_tensors, total_loss

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    config = ModelConfig()
    model = CampusModel(config).train()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=steps, eta_min=lr * 0.05)
    weights = weights or LossWeights()
    mock_graph = prepare_graph(build_mock_campus_graph())

    window: Dict[str, float] = {}
    window_count = 0
    started = time.time()

    for step in range(1, steps + 1):
        optimiser.zero_grad()
        for _ in range(graphs_per_step):
            graph = mock_graph if rng.random() < mock_graph_prob else prepare_graph(random_campus_graph(rng))
            tensors = graph_tensors(graph, min_gap)
            raw = model(
                torch.as_tensor(graph.node_inputs, dtype=torch.float32),
                torch.as_tensor(graph.edge_index),
                torch.as_tensor(graph.edge_inputs, dtype=torch.float32),
                torch.randn(samples_per_graph, graph.num_nodes, config.latent_dim),
                torch.randn(samples_per_graph, config.latent_dim),
            )
            loss, parts = total_loss(raw, tensors, weights)
            (loss / graphs_per_step).backward()
            parts["total"] = float(loss.detach())
            for name, value in parts.items():
                window[name] = window.get(name, 0.0) + value
            window_count += 1

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimiser.step()
        scheduler.step()

        if log_every and (step % log_every == 0 or step == steps):
            means = {name: value / window_count for name, value in window.items()}
            summary = "  ".join(f"{name}={value:.4f}" for name, value in means.items())
            print(f"step {step:5d}/{steps}  {summary}  ({time.time() - started:.0f}s)")
            if step != steps:
                window, window_count = {}, 0

    if out_path is not None:
        save_params(model.to_params(), out_path)
        print(f"saved weights -> {out_path}")

    return {name: value / max(window_count, 1) for name, value in window.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the ArchOpt campus GNN.")
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--graphs-per-step", type=int, default=4)
    parser.add_argument("--samples-per-graph", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=DEFAULT_WEIGHTS_PATH)
    parser.add_argument("--log-every", type=int, default=250)
    args = parser.parse_args()
    train(
        steps=args.steps,
        graphs_per_step=args.graphs_per_step,
        samples_per_graph=args.samples_per_graph,
        lr=args.lr,
        seed=args.seed,
        out_path=args.out,
        log_every=args.log_every,
    )


if __name__ == "__main__":
    main()
