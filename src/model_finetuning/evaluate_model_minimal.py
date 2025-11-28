#!/usr/bin/env python3
import os
import sys
import argparse
import torch
from PIL import Image
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CADRL'))
from utils.model_utils import load_model, load_checkpoint_into_model

def generate_code(model, processor, image, text_prompt, max_new_tokens=4096, temperature=1.0):
    messages = [[
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": text_prompt}
            ]
        }
    ]]
    
    texts = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=texts,
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    
    if hasattr(model, 'device'):
        device = model.device
    else:
        device = next(model.parameters()).device
    
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "use_cache": True,
        "pad_token_id": processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id,
    }
    
    if temperature <= 0.01:
        generation_kwargs["do_sample"] = False
    else:
        generation_kwargs["temperature"] = temperature
        generation_kwargs["do_sample"] = True
    
    with torch.inference_mode():
        generated_ids = model.generate(**inputs, **generation_kwargs)
    
    generated_ids_trimmed = generated_ids[0][len(inputs["input_ids"][0]):]
    generated_text = processor.decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    
    return generated_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--text_prompt", type=str, default="Generate the CADQuery code needed to create the CAD for the provided image.")
    parser.add_argument("--checkpoint_path", type=str, default="/home/apalapar/orcd/scratch/FedVLM4CAD-Code/checkpoints/centralized/full_finetune_full/final_model.pt")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen3-VL-2B-Instruct")
    parser.add_argument("--max_new_tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=1.0)
    
    args = parser.parse_args()
    
    processor = AutoProcessor.from_pretrained(args.base_model)
    
    torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    
    model = load_model(
        args.base_model,
        torch_dtype=torch_dtype,
        device_map="auto",
        quantization_config=None,
        use_flash_attention=True
    )
    
    print(f"Loading checkpoint from: {args.checkpoint_path}")
    load_checkpoint_into_model(model, args.checkpoint_path)
    
    model.eval()
    
    image = Image.open(args.image_path).convert("RGB")
    
    generated_code = generate_code(
        model, processor, image, args.text_prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature
    )
    
    print(generated_code)

if __name__ == "__main__":
    main()

