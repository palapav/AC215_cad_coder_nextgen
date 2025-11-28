import re
import subprocess
import os

TEST_TEMPLATE = """
{code}
cq.exporters.export(solid, {file_name})
"""

OCC_IOU_TEMPLATE = """
from Inference.Geom._OCC_IOU import align_shapes, load_step_file

solid_gt = load_step_file("{ground_truth_step_path}")
solid_gen = load_step_file("{generated_step_path}")

IOU = align_shapes(solid_gen, solid_gt)[1]
"""

def extract_code(text):
    # Use regex to find the code block
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return text

def run_code(code):
    # Given CadQuery code, will return whether it ran successfully or not
    try:
        result = subprocess.run(
            ["/home/adoris/.conda/envs/inference_scaling/bin/python", "-c", code], #TODO: pass conda environment in as argument?
            capture_output=True,
            text=True,
            timeout=60 # if code takes more than 1 minute to run, log as failure
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        return 1

def compute_iou(ground_truth_step_path, mg_step_path, timeout=60):
    # Computes IoU given two steps, returns 0 if error thrown or timeout reached
    code = f"""
import sys
import os
sys.path.insert(0, r"{os.getcwd()}")

import cadquery as cq
from Inference.Geom._IOU import align_shapes
try:
    gt = cq.importers.importStep(r"{ground_truth_step_path}")
    mg = cq.importers.importStep(r"{mg_step_path}")
    _, iou = align_shapes(mg, gt)
    print(iou)
except Exception as e:
    print("[ERROR]", e)
    print(0.0)
"""

    try:
        result = subprocess.run(
            ["/home/adoris/.conda/envs/inference_scaling/bin/python", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        # Parse last printed float as IoU
        for line in reversed(result.stdout.strip().splitlines()):
            try:
                return float(line)
            except ValueError:
                continue
        return 0.0
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] IoU computation exceeded {timeout}s for {ground_truth_step_path} and {mg_step_path}")
        return 0.0