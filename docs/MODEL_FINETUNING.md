## Qwen3-VL Fine-Tuning Results on the GenCAD-Code Dataset

> **Note:** Results are preliminary and part of ongoing research on scaling Qwen3-VL models for CAD code generation. LoRA training logs are excluded from the repository because they relate to an in-progress study. Additionally, please take a look at the ../src/model_finetuning folder for more details.

## Overview

This document summarizes fine-tuning for the Qwen3-VL 2B, 4B, and 8B models on the GenCAD-Code dataset for CAD code generation. Both full fine-tuning and LoRA training were evaluated to understand performance, scaling, and stability.

---

# **Dataset**

* **Dataset:** GenCAD-Code (Version 1 via DVC)
* **Training Samples:** 147,289
* **Validation Set:** 500 held-out samples
* **Format:** Image → CADQuery (JSONL)

---

# **Model Variants & Training Configuration**

## **Model Sizes**

| Model                | Parameters | Approx GPU Memory | Training Time |
| -------------------- | ---------- | ----------------- | ------------- |
| Qwen3-VL-2B-Instruct | 2B         | ~16 GB            | ~5 hours      |
| Qwen3-VL-4B-Instruct | 4B         | ~32 GB            | ~8 hours      |
| Qwen3-VL-8B-Instruct | 8B         | ~64 GB            | ~15 hours     |

---

## **Training Setup**

```yaml
Hardware:
  GPUs: 4× NVIDIA H100 80GB
  CUDA: 12.4
  Framework: PyTorch 2.6.0

Hyperparameters:
  Epochs: 1 (Full FT), 3 (LoRA)
  Batch size per GPU: 4
  Gradient accumulation: 16
  Effective batch size: 256
  Learning rate: 2e-5
  Weight decay: 0.0
  Warmup steps: 100
  Max gradient norm: 1.0
  Max sequence length: 4096

Model Configuration:
  Vision encoder: Frozen
  Precision: bfloat16
  Optimizer: AdamW
  Scheduler: Constant with warmup
  Distributed: FSDP
```

---

# **Validation Loss Results**

| Model        | Method           | Validation Loss |
| ------------ | ---------------- | --------------- |
| **Qwen3-2B** | LoRA (3 epochs)  | **0.081**       |
| **Qwen3-2B** | Full Fine-tuning | **0.064**       |
| **Qwen3-4B** | LoRA (3 epochs)  | **0.086**       |
| **Qwen3-8B** | LoRA (3 epochs)  | **0.0699**      |
| **Qwen3-8B** | Full Fine-tuning | **0.058**       |

---

# **Model Evaluation Results (Test100)**

Below are the fine-tuning results for all Qwen3-VL models evaluated on the GenCAD-Code Test100 set.

---

## **Performance Summary**

| Model           | Training Method | Valid Sample Rate (%) | Mean IOU | Adjusted IOU |
| --------------- | --------------- | --------------------- | -------- | ------------ |
| **Qwen3-VL-2B** | LoRA            | 89                    | 0.685    | **0.610**    |
| **Qwen3-VL-2B** | Full FT         | 90                    | 0.715    | **0.642**    |
| **Qwen3-VL-4B** | LoRA            | 88                    | 0.680    | **0.605**    |
| **Qwen3-VL-8B** | LoRA            | 89                    | 0.705    | **0.630**    |
| **Qwen3-VL-8B** | Full FT         | 91                    | 0.734    | **0.668**    |

---

# **Training Curve Observations**

### **2B Models**

* Full fine-tuning reaches a noticeably lower loss than LoRA.
* Training is smooth with stable convergence.

### **4B LoRA**

* Exhibits higher variance and the highest validation loss among all models.

### **8B Models**

* LoRA performs reasonably well but remains limited by adapter bottlenecks.
* Full fine-tuning provides the strongest convergence and lowest validation loss.

---

# **Deployment Implications**

## **Current Production Deployment**

The **Qwen3-VL-2B Full Fine-tuned** model is currently used in production due to:

1. **Best balance of latency, cost, and accuracy**
2. Compatibility with mid-tier GPUs (A10G / L4)
3. Fast inference and strong output consistency
4. High validity (~90%) suitable for CAD code generation workloads

---

## **Path Toward 8B Deployment**

| Phase       | Model        | Infra            | Purpose                             |
| ----------- | ------------ | ---------------- | ----------------------------------- |
| **Current** | 2B Full FT   | Modal / GKE A10G | Production baseline                 |
| **Next**    | 8B Full FT   | A100/H100        | Quality-critical generation         |
| **Future**  | 8B Quantized | INT4/INT8        | Production-ready high-accuracy tier |

## **Recommended Serving Stack for 8B**

* **vLLM** (continuous batching, high throughput)
* **TensorRT-LLM** (GPU-optimized kernels)
* **Token streaming** for interactive UX
* **Quantization** to reduce VRAM footprint

---

# **Reproducibility**

### Training Command Example

```bash
accelerate launch --num_processes=4 centralized_train.py \
  --base_model Qwen/Qwen3-VL-2B-Instruct \
  --output_dir checkpoints/qwen3_2B \
  --num_epochs 1 \
  --batch_size 4 \
  --gradient_accumulation_steps 16 \
  --lr 2e-5 \
  --freeze_vision \
  --gradient_checkpointing \
  --eval_steps 500 \
  --log_to_wandb
```

### Evaluation Command Example

```bash
python evaluate_model.py \
  --model_path checkpoints/qwen3_2B/final_model.pt \
  --test_data data/partitioned/test \
  --output_file results/eval/qwen3_2B.json
```

---

# **Repository Structure**

```
src/model_finetuning/
├── centralized_train.py
├── evaluate_model.py
├── evaluate_model_minimal.py
├── requirements.txt
├── CADRL/
│   ├── DataUtils/
│   ├── Inference/
│   └── Trainers/
└── results/
    ├── train/
    └── eval/
```

---

# **References**

* Qwen3-VL Models — [https://huggingface.co/Qwen](https://huggingface.co/Qwen)
* GenCAD-Code Dataset — [https://huggingface.co/datasets/GenCAD/GenCAD-Code](https://huggingface.co/datasets/GenCAD/GenCAD-Code)
* CAD-Coder Paper — `references/cad_coder_paper.pdf`

---

# **Production ML Workflow (GKE)**

This section summarizes the production-ready ML workflow we ship on GKE for the Qwen3-VL models. It is present in the repo but kept **disabled by default** to avoid unintended runs.

## Components
- **Orchestration:** `infrastructure/kubernetes/ml-workflow/` manifests (CronJob, ConfigMap, RBAC, PVC) plus backend hooks in `src/model_finetuning/ml_workflow/`.
- **Data preprocessing:** Jobs pull the latest GenCAD-Code partitions (via DVC/GCS), normalize image/code pairs, and write to shared PVC.
- **Training:** Qwen3-VL-2B training/eval scripts (CPU-friendly configs in tests; GPU-ready in production) with checkpoints stored to PVC/GCS.
- **Evaluation:** Validation metrics (syntax validity, IOU-style geometry proxies) written to artifacts and compared against thresholds defined in `ml_workflow/config.py`.
- **Validation gate:** `ModelValidator` enforces minimum quality before promotion.
- **Deployment step (mocked hooks):** `ModelDeployment` contains stubs for promoting to Modal or updating GKE images. Hooks are wired but no-op unless explicitly enabled.

## Triggers and Safety
- **Primary trigger:** Scheduled CronJob (suspended by default). Enable by patching `ml-retraining-job` `spec.suspend=false`.
- **Manual trigger:** Apply the job manifest or run the module entrypoint locally.
- **CI gating:** No automatic deploy on PRs; deployment can be invoked only after CI success and explicit enablement.

## Operational Notes
- PVC is optional; artifacts can be redirected to GCS.
- Secrets (tokens, URIs) are expected via Kubernetes secrets; tests use mocks.
- Default concurrency is minimal to control cost; adjust CronJob resources if running on GPUs.
