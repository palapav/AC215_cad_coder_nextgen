# Model Fine-Tuning: Qwen3-VL for CAD Code Generation

## Overview

This document describes the fine-tuning process for Qwen3-VL Vision-Language Models on the GenCAD-Code dataset for CAD code generation. We fine-tuned three model variants (2B, 4B, 8B parameters) using full fine-tuning on NVIDIA H100 GPUs.

## Training Process

### Dataset

- **Dataset**: GenCAD-Code (Version 1 - static baseline from DVC)
- **Total Samples**: 147,289 training samples
- **Validation**: 500 subsampled examples (for efficiency)
- **Format**: Image-to-CADQuery code pairs in JSONL format

### Model Variants

| Model | Parameters | GPU Memory | Training Time |
|-------|------------|------------|---------------|
| Qwen3-VL-2B-Instruct | 2 billion | ~16 GB | ~5 hours |
| Qwen3-VL-4B-Instruct | 4 billion | ~32 GB | ~8 hours |
| Qwen3-VL-8B-Instruct | 8 billion | ~64 GB | ~15 hours |

### Training Configuration

```yaml
Hardware:
  GPUs: 4x NVIDIA H100 80GB HBM3
  CUDA: 12.4
  Framework: PyTorch 2.6.0

Hyperparameters:
  Epochs: 1
  Batch size per GPU: 4
  Gradient accumulation: 16
  Effective batch size: 256
  Learning rate: 2e-5
  Weight decay: 0.0
  Warmup steps: 100
  Max gradient norm: 1.0
  Max sequence length: 4096

Model Configuration:
  Vision encoder: Frozen (only language model trained)
  Precision: bfloat16
  Optimizer: AdamW
  Scheduler: Constant with warmup
```

### Training Pipeline

1. **Data Loading**: Combined training dataset loaded from partitioned HuggingFace format
2. **Preprocessing**: Images processed with Qwen-VL processor; code wrapped in assistant response template
3. **Training**: Distributed training across 4 GPUs using FSDP (Fully Sharded Data Parallel)
4. **Validation**: Loss evaluated every 500 steps on held-out validation set
5. **Checkpointing**: Final model saved as PyTorch checkpoint

## Results

### Evaluation Metrics

We evaluate models using:
- **Valid Sample Rate (%)**: Percentage of generated code that executes without errors
- **Mean IOU**: Intersection over Union between generated and ground truth CAD models
- **Median IOU**: Robust central tendency measure for IOU
- **Mean IOU (Adjusted)**: IOU adjusted for failed samples (set to 0)

### Model Performance Comparison

| Model | Valid Rate | Mean IOU | Median IOU | Adjusted IOU |
|-------|------------|----------|------------|--------------|
| **Qwen3-VL-2B** | 96.97% | 0.563 | 0.617 | 0.546 |
| **Qwen3-VL-4B** | 97.30% | 0.586 | 0.640 | 0.567 |
| **Qwen3-VL-8B** | 98.00% | 0.628 | 0.676 | 0.605 |

### Error Analysis

| Error Type | 2B | 4B | 8B |
|------------|-----|-----|-----|
| Failed Generation | 1.76% | 1.55% | 1.20% |
| OCC Errors | 0.88% | 0.82% | 0.60% |
| Timeouts | 0.39% | 0.38% | 0.25% |
| None Solids | 0.00% | 0.00% | 0.00% |

### Key Findings

1. **Scaling Benefits**: Larger models consistently improve both valid sample rate and IOU
2. **Error Reduction**: 8B model reduces generation failures by 32% compared to 2B
3. **Quality-Speed Tradeoff**: 2B offers 3x faster inference with ~10% lower IOU
4. **High Validity**: All models achieve >96% valid code generation rate

## Deployment Implications

### Current Production Strategy

We deploy the **2B Qwen3-VL-Instruct** model in production (Modal Labs) because:

1. **Quality-Latency-Cost Tradeoff**: 2B offers strong performance (96.97% valid, 0.563 IOU) with significantly lower compute costs
2. **Rapid Iteration**: Smaller model enables faster experimentation with prompts and system integration
3. **GPU Requirements**: 2B fits on A10G GPUs (~24GB VRAM), while 8B requires A100 (~40GB)

### Future Deployment Roadmap

| Phase | Model | Infrastructure | Use Case |
|-------|-------|----------------|----------|
| **Current** | 2B | Modal Labs/GKE (A10G) | Production baseline |
Cost-optimized premium |

### Scaling Considerations

**For 8B Production Deployment:**
- **Infrastructure**: GKE with high-memory GPUs or Vertex AI endpoints
- **Optimization**: INT8/INT4 quantization to reduce VRAM requirements
- **Serving**: vLLM or TensorRT-LLM for optimized inference
- **Streaming**: Token streaming for improved perceived latency

### Model Selection Guidelines

| Scenario | Recommended Model | Rationale |
|----------|-------------------|-----------|
| Cost-sensitive production | 2B | Best cost-per-request |
| Quality-critical applications | 8B | Highest IOU and validity |
| Real-time applications | 2B | Lowest latency |
| Batch processing | 8B | Quality over speed |

## Data Versioning Integration

### Training Data Source

- **Version**: V1 (original, static GenCAD-Code dataset)
- **Tracking**: DVC (Data Version Control)
- **Reproducibility**: Training uses exact checksummed dataset version

### Why V1 (Static Dataset)?

1. **Consistency**: Fine-tuning on stable baseline ensures reproducible results
2. **Quality Control**: Original dataset is curated and validated
3. **Comparison**: Enables fair comparison across model variants

### Future Retraining

When retraining with V2 (user-extended dataset):
1. Pull latest dataset version: `dvc checkout`
2. Verify data integrity: `dvc status`
3. Update training scripts to point to V2 paths
4. Document version in training logs

## Reproducibility

### Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd cad-coder-nextgen/src/model_finetuning

# Create conda environment
conda create -n cadcoder python=3.10
conda activate cadcoder

# Install dependencies (GPU cluster)
pip install -r requirements.txt
```

### Training Command

```bash
# 2B Model (example)
accelerate launch --num_processes=4 centralized_train.py \
    --base_model Qwen/Qwen3-VL-2B-Instruct \
    --output_dir ./checkpoints/qwen3_2B \
    --num_epochs 1 \
    --batch_size 4 \
    --gradient_accumulation_steps 16 \
    --lr 2e-5 \
    --freeze_vision \
    --gradient_checkpointing \
    --eval_steps 500 \
    --log_to_wandb
```

### Evaluation Command

```bash
python evaluate_model.py \
    --model_path ./checkpoints/qwen3_2B/final_model.pt \
    --test_data ./data/partitioned/test \
    --output_file results/eval/qwen3_2B.json
```

## File Structure

```
src/model_finetuning/
├── centralized_train.py      # Main training script
├── evaluate_model.py         # Full evaluation with IOU
├── evaluate_model_minimal.py # Lightweight evaluation
├── requirements.txt          # Dependencies
├── finetuning.md            # (Deprecated - see this document)
├── CADRL/                   # Core training library
│   ├── DataUtils/           # Dataset and collator classes
│   │   ├── Datasets.py      # CADLMDataset, MinimalImageCADDataset
│   │   └── Collators.py     # QwenVLCollator
│   ├── Inference/           # Evaluation utilities
│   │   ├── Geom/            # IOU computation (OCC-based)
│   │   ├── VLLMClient.py    # vLLM inference client
│   │   └── IOUClient.py     # IOU computation client
│   └── Trainers/            # Training loops
│       └── SFT/             # Supervised fine-tuning
├── utils/                   # Configuration and utilities
│   ├── config.py            # Default hyperparameters
│   ├── model_utils.py       # Model loading helpers
│   └── patches.py           # Accelerate compatibility patches
└── results/                 # Training and evaluation outputs
    ├── train/               # Training logs (.out, .err)
    └── eval/                # Evaluation results (.json)
```

## References

- [Qwen3-VL Model](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
- [GenCAD-Code Dataset](https://huggingface.co/datasets/GenCAD/GenCAD-Code)
- [CAD-Coder Paper](../references/cad_coder_paper.pdf)

