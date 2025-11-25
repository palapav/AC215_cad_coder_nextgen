#!/usr/bin/env bash

set -euo pipefail

curl -X POST "http://localhost:8000/generate_cad" \
  -H "Content-Type: application/json" \
  -d '{
        "prompt": "Generate the CadQuery code needed to create the CAD for the provided image. Just the code, no other words.",
        "user_id": "test-user",
        "model_choice": "qwen",
        "image_path": "/Users/aditya/Documents/apcomp215/cad-coder-nextgen/src/model_inference/qwen/15.png"
      }'
