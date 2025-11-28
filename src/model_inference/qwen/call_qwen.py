import modal
from pathlib import Path

APP_NAME = "cad-coder-qwen3"  # must match APP_NAME in modal_app.py

def main():
    # Look up the deployed function in Modal
    qwen_modal_infer = modal.Function.from_name(APP_NAME, "qwen_modal_infer")

    image_path = "src/model_inference/qwen/15.png"
    img_bytes = Path(image_path).read_bytes()

    result = qwen_modal_infer.remote(
        prompt="Generate the CadQuery code needed to create the CAD for the provided image. Just the code, no other words.",
        image_bytes=img_bytes,
        image_format="PNG",
        max_new_tokens=4096,
        temperature=0.0,
    )

    print("------ CAD-Coder (Modal) Output ------")
    print(result)

if __name__ == "__main__":
    main()
