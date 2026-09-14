"""
ml/models/campus_model.py
=========================
Wires GNN encoder → layout decoder into one model.

    raw = model(node_inputs, edge_index, edge_inputs, z_node, z_graph)   # [K, N, 3]

Weights live in a plain .npz file keyed by torch state_dict names, so the same
checkpoint drives both the torch module (training) and the NumPy forward pass
(inference without PyTorch).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np

from ml.models.features import EDGE_INPUT_DIM, NODE_INPUT_DIM, PreparedGraph
from ml.models.gnn_encoder import HIDDEN_DIM, NUM_LAYERS, TORCH_AVAILABLE, Params, encode_numpy
from ml.models.layout_decoder import DECODER_OUTPUTS, LATENT_DIM, decode_numpy

if TORCH_AVAILABLE:
    import torch
    from torch import nn

    from ml.models.gnn_encoder import GNNEncoder
    from ml.models.layout_decoder import LayoutDecoder

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "weights" / "campus_model.npz"


@dataclass(frozen=True)
class ModelConfig:
    node_dim: int = NODE_INPUT_DIM
    edge_dim: int = EDGE_INPUT_DIM
    hidden_dim: int = HIDDEN_DIM
    num_layers: int = NUM_LAYERS
    latent_dim: int = LATENT_DIM


def param_shapes(config: ModelConfig = ModelConfig()) -> Dict[str, Tuple[int, ...]]:
    """Expected parameter names and shapes (matches CampusModel.state_dict())."""
    shapes: Dict[str, Tuple[int, ...]] = {}

    def linear(name: str, fan_in: int, fan_out: int) -> None:
        shapes[f"{name}.weight"] = (fan_out, fan_in)
        shapes[f"{name}.bias"] = (fan_out,)

    h, latent = config.hidden_dim, config.latent_dim
    linear("encoder.input_proj", config.node_dim, h)
    for layer in range(config.num_layers):
        linear(f"encoder.layers.{layer}.message", h + config.edge_dim, h)
        linear(f"encoder.layers.{layer}.update", 2 * h, h)
    linear("decoder.hidden1", 2 * h + 2 * latent, h)
    linear("decoder.hidden2", h, h)
    linear("decoder.out", h, DECODER_OUTPUTS)
    return shapes


def init_params(config: ModelConfig = ModelConfig(), seed: int = 0) -> Params:
    """Random weights (PyTorch-style uniform init). Used when no checkpoint exists."""
    rng = np.random.default_rng(seed)
    shapes = param_shapes(config)
    params: Params = {}
    for name, shape in shapes.items():
        fan_in = shapes[name.rsplit(".", 1)[0] + ".weight"][1]
        bound = 1.0 / np.sqrt(fan_in)
        params[name] = rng.uniform(-bound, bound, size=shape)
    return params


def save_params(params: Params, path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **{k: np.asarray(v, dtype=np.float32) for k, v in params.items()})


def load_params(path: Union[str, Path], config: ModelConfig = ModelConfig()) -> Params:
    """Load an .npz checkpoint and check it matches `config`."""
    with np.load(Path(path)) as data:
        params = {k: data[k].astype(np.float64) for k in data.files}
    expected = param_shapes(config)
    if set(params) != set(expected):
        raise ValueError(f"Checkpoint {path} has parameters {sorted(params)}, expected {sorted(expected)}")
    for name, shape in expected.items():
        if params[name].shape != shape:
            raise ValueError(f"Checkpoint {path}: {name} has shape {params[name].shape}, expected {shape}")
    return params


def forward_numpy(
    params: Params,
    graph: PreparedGraph,
    z_node: np.ndarray,
    z_graph: np.ndarray,
    config: ModelConfig = ModelConfig(),
) -> np.ndarray:
    h = encode_numpy(params, graph.node_inputs, graph.edge_index, graph.edge_inputs, config.num_layers)
    return decode_numpy(params, h, z_node, z_graph)


if TORCH_AVAILABLE:

    class CampusModel(nn.Module):
        def __init__(self, config: ModelConfig = ModelConfig()):
            super().__init__()
            self.config = config
            self.encoder = GNNEncoder(config.node_dim, config.edge_dim, config.hidden_dim, config.num_layers)
            self.decoder = LayoutDecoder(config.hidden_dim, config.latent_dim)

        def forward(
            self,
            node_inputs: "torch.Tensor",
            edge_index: "torch.Tensor",
            edge_inputs: "torch.Tensor",
            z_node: "torch.Tensor",
            z_graph: "torch.Tensor",
        ) -> "torch.Tensor":
            h = self.encoder(node_inputs, edge_index, edge_inputs)
            return self.decoder(h, z_node, z_graph)

        @classmethod
        def from_params(cls, params: Params, config: ModelConfig = ModelConfig()) -> "CampusModel":
            model = cls(config)
            model.load_state_dict({k: torch.as_tensor(v, dtype=torch.float32) for k, v in params.items()})
            return model

        def to_params(self) -> Params:
            return {k: v.detach().cpu().numpy().astype(np.float64) for k, v in self.state_dict().items()}


def forward(
    params: Params,
    graph: PreparedGraph,
    z_node: np.ndarray,
    z_graph: np.ndarray,
    config: ModelConfig = ModelConfig(),
    backend: str = "auto",
) -> np.ndarray:
    """
    Run the model and return raw logits [K, N, 3] as a NumPy array.

    backend: "auto" (torch when installed, else NumPy), "torch" or "numpy".
    """
    if backend not in ("auto", "torch", "numpy"):
        raise ValueError(f"Unknown backend {backend!r}")
    if backend == "torch" and not TORCH_AVAILABLE:
        raise RuntimeError("backend='torch' requested but PyTorch is not installed")
    if backend == "numpy" or not TORCH_AVAILABLE:
        return forward_numpy(params, graph, z_node, z_graph, config)

    model = CampusModel.from_params(params, config).eval()
    with torch.no_grad():
        raw = model(
            torch.as_tensor(graph.node_inputs, dtype=torch.float32),
            torch.as_tensor(graph.edge_index, dtype=torch.long),
            torch.as_tensor(graph.edge_inputs, dtype=torch.float32),
            torch.as_tensor(z_node, dtype=torch.float32),
            torch.as_tensor(z_graph, dtype=torch.float32),
        )
    return raw.numpy().astype(np.float64)
