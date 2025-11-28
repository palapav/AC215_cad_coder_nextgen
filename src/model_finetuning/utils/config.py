#!/usr/bin/env python3
"""Configuration defaults and utilities"""

# Default model (Qwen3-VL-8B-Instruct for 4x H100 GPUs)
DEFAULT_MODEL = "Qwen/Qwen3-VL-8B-Instruct"

# Default training hyperparameters
TRAINING_DEFAULTS = {
    "batch_size": 2,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-5,
    "weight_decay": 0.0,
    "warmup_steps": 100,
    "max_grad_norm": 1.0,
    "max_len": 4096,
    "num_epochs": 1,
    "checkpoint_steps": 1000,  # Sparse checkpointing (every 1000 steps)
    "num_points": 256,
}

# Federated learning defaults
FEDERATED_DEFAULTS = {
    "num_rounds": 5,
    "client_epochs": 1,
}

# Default data paths (relative to project root)
DATA_PATHS = {
    "partitioned": "./data/partitioned",
    "client1": "./data/partitioned/client1",
    "client2": "./data/partitioned/client2",
    "combined": "./data/partitioned/combined",  # Cache for combined training data
    "validation": "./data/partitioned/validation",
    "test": "./data/partitioned/test",
}

# WandB defaults
WANDB_DEFAULTS = {
    "centralized_project": "Centralized-CADCoder",
    "federated_project": "FedAvg-CADCoder",
    "evaluation_project": "FedAvg-CADCoder-Eval",
}

# Evaluation defaults
EVALUATION_DEFAULTS = {
    "n_samples": 1,
    "n_workers": 20,
    "timeout": 15,
    "temperature": 1.0,
    "max_new_tokens": 4096,
}
