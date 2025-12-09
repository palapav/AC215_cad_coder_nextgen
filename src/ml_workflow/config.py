#!/usr/bin/env python3
"""Configuration for ML Workflow - Performance thresholds and settings"""

# Performance thresholds for model deployment
PERFORMANCE_THRESHOLDS = {
    "min_valid_sample_rate": 0.95,  # 95% minimum valid sample rate
    "min_mean_iou": 0.50,  # 0.50 minimum mean IOU
    "min_median_iou": 0.55,  # 0.55 minimum median IOU
    "max_failed_generation_rate": 0.05,  # 5% maximum failed generation rate
}

# Training configuration
TRAINING_CONFIG = {
    "base_model": "Qwen/Qwen3-VL-2B-Instruct",
    "num_epochs": 1,
    "batch_size": 2,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-5,
    "checkpoint_steps": 1000,
    "eval_steps": 500,  # Evaluate every 500 steps
    "val_samples": 1000,  # Use 1000 validation samples
    # WandB configuration for experiment tracking
    "log_to_wandb": True,  # Enable WandB logging
    "wandb_project": "CAD-Coder-ML-Workflow",  # WandB project name
}

# Evaluation configuration
EVALUATION_CONFIG = {
    "n_samples": 1,
    "n_workers": 20,
    "timeout": 15,
    "temperature": 1.0,
    "max_new_tokens": 4096,
    "batch_size": 8,
}

# Testing/Development configuration
# Set these to limit samples for quick testing of the pipeline
# Set to None to use full dataset
# 
# Usage:
#   - Command line: --max-training-samples 100 --max-test-samples 50
#   - Or set here for default test mode behavior
TEST_CONFIG = {
    "max_training_samples": None,  # Limit training samples (e.g., 100 for quick test)
    "max_test_samples": None,      # Limit test samples for evaluation (e.g., 50 for quick test)
    "max_val_samples": 1000,       # Already limited in TRAINING_CONFIG, kept for consistency
}

# Data paths (relative to project root)
DATA_PATHS = {
    "client1": "./data/partitioned/client1",
    "client2": "./data/partitioned/client2",
    "combined": "./data/partitioned/combined",
    "validation": "./data/partitioned/validation",
    "test": "./data/partitioned/test",
}

# Modal Labs configuration
MODAL_CONFIG = {
    "app_name": "cad-coder-ml-workflow",
    "volume_name": "cad-coder-ml-models",
    "gpu_type": "A100",  # For 2B model
    "timeout": 3600,  # 1 hour timeout for training
}

# GCP Mock configuration
GCP_MOCK_CONFIG = {
    "trigger_topic": "ml-retraining-trigger",  # Mock Pub/Sub topic
    "deployment_topic": "ml-deployment-trigger",  # Mock Pub/Sub topic
    "project_id": "cad-coder-nextgen",  # Mock project ID
    "region": "us-central1",
}

# Workflow status tracking
WORKFLOW_STATUS = {
    "PENDING": "pending",
    "PREPROCESSING": "preprocessing",
    "TRAINING": "training",
    "EVALUATING": "evaluating",
    "VALIDATING": "validating",
    "DEPLOYING": "deploying",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "REJECTED": "rejected",  # Failed validation
}

