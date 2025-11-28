#!/usr/bin/env bash
set -euo pipefail

# macOS-compatible base64
IMAGE_B64=$(base64 < ../model_inference/qwen/15.png | tr -d '\n')

JSON=$(cat <<EOF
{
  "prompt": "Generate the CadQuery code needed to create the CAD for a cube.",
  "user_id": "test-user",
  "model_choice": "llava",
}
EOF
)

curl -X POST "http://localhost:8000/generate_cad" \
  -H "Content-Type: application/json" \
  -d "$JSON"