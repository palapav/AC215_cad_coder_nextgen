
import torch
import time
import statistics
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any, Optional
from vllm import LLM, SamplingParams
from datasets import load_dataset
from DataUtils.Datasets import CADLMDataset
from Inference import extract_code
from Utils import question_id_to_step_path
import json
import subprocess
from Inference import run_code, compute_iou
import os
from joblib import Parallel, delayed, parallel_backend
import psutil
from tqdm import tqdm
from collections import defaultdict
import shutil
from tqdm_joblib import tqdm_joblib
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class InferenceScaling:
    """
    Manages and runs inference scaling experiments for Hugging Face models.
    """

    def __init__(
        self,
        model_path: str,
        data_path: str,
        save_dir: str,
        n_parallel: int,
        use_vllm: bool = True
    ):
        """
        Initialize the inference scaling experiment manager.
        """
        
        if not use_vllm:
            raise ValueError("Inference without vllm not yet supported")

        self.model_path = model_path
        self.data_path = data_path
        self.use_vllm = use_vllm
        self.save_dir = save_dir
        self.n_parallel = n_parallel
        self.individual_experiment_path = None
        
        print(f"--- Inference Scaling Initialized ---")
        print(f"Model: {self.model_path}")
        print(f"Dataset: {self.data_path}")
        print(f"Save Dir: {self.save_dir}")
        print(f"Num jobs parallel: {self.n_parallel}")
        print(f"Use VLLM: {self.use_vllm}")
        print("----------------------------")

        # Load VLLM model and dataset
        self.model = self._load_model()
        self.dataset = self._load_dataset()

    def _load_model(self):
        """Loads the model from HuggingFace into VLLM LLM"""
        
        model = None
        
        if self.use_vllm:
            print("Setting up VLLM model...")
            model = LLM(model=self.model_path,
                        tensor_parallel_size=torch.cuda.device_count(),
                        max_model_len=4096*2,
                        dtype='bfloat16')
            print(f"Successfully loaded {self.model_path} as VLLM model")

        return model
    
    def _load_dataset(self):
        print("Loading dataset...")
        data = load_dataset(self.data_path)
        print(f"Successfully loaded {self.data_path} dataset")
        return data

    def run_best_of_n(self, num_generations: int, temperature: float, top_p: float, max_tokens: int, split: str):
        """
        Runs n inference samples per test question and reports the max score
        """
        
        # Make dir for this run
        self.individual_experiment_path = f"{self.save_dir}/split{split}_num{str(num_generations)}_temp{str(temperature)}_topp{str(top_p)}"
        os.makedirs(self.individual_experiment_path, exist_ok=True)
        
        # Get the dataset prompts ready
        data = self.dataset[split].to_list()
        ids = [ex["id"] for ex in data]
        dataset = CADLMDataset(data, None)
        prompts, gts = dataset.gather_vllm_data(image_type='png')
        
        # Get the ground truth step files
        # TODO: just use code files as gt? generate once and compare?
        if split == "test100":
            gt_step_paths, deepcad_ids = question_id_to_step_path('/orcd/data/faez/001/annie/llava/eval/gencad_cadquery/cadquery_test_data_subset100.jsonl', ids, '/orcd/compute/faez/001/annie/DeepCAD/data/steps/')
        else:
            raise NotImplementedError("gt step path not implemented for this split!")
        
        # Set up sampling parameters
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n=num_generations
        )
        
        print("Running inference...")
        results = self.model.chat(prompts, sampling_params=sampling_params)
        print("Inference completed!")
        
        print("Processing results...")
        complete_response = []
        code_only_response = []
        
        for result in results:
            if result.outputs:
                
                # Collect all generated outputs (texts) for this prompt
                gen_codes = [output.text for output in result.outputs]
                complete_response.append(gen_codes)

                # Extract code from each generation
                code_only = [extract_code(code) for code in gen_codes]
                code_only_response.append(code_only)
            else:
                complete_response.append([])
                code_only_response.append([])

        # Group and dump all of the results together in one place
        complete_results = [
            {"prompt": p, "complete_repsonse": cr, "code_only": code, "ground_truth": gt, "gt_step_path": gt_step, "deepcad_id": did}
            for p, cr, code, gt, gt_step, did in zip(prompts, complete_response, code_only_response, gts, gt_step_paths, deepcad_ids)
        ]
        with open(f"{self.individual_experiment_path}/full_results.json", "w") as f:
            json.dump(complete_results, f, indent=2)
        print("Finished processing results.")
        
        print("Computing metrics...")
        vsr, iou = self._calculate_results(complete_results, num_generations)
        print("Finished computing metrics")
        return vsr, iou


    def _calculate_results(self, results, num_generations):
        
        # Make a directory to save the step files
        step_root = self.individual_experiment_path + "/steps"
        os.makedirs(step_root, exist_ok=True)

        # Run all the code that the model generated
        all_codes = []
        for result in results:
            code_responses = result["code_only"]
            for i, code in enumerate(code_responses):
                deepcad_id = result["deepcad_id"].split("/")[1]
                step_save_path = deepcad_id + f"_{i+1}.step"
                code += f"\ncq.exporters.export(solid, '{step_root}/{step_save_path}')" # Add on code to save as a step file
                all_codes.append(code)
        
        print("Starting VSR computation...")
        with tqdm_joblib(tqdm(desc="Running code", total=len(all_codes))) as progress_bar:
            outputs = Parallel(n_jobs=min(self.n_parallel // 2, len(all_codes)))(
                delayed(run_code)(code) for code in all_codes
            )
        all_vsr = [0 in outputs[i:i+num_generations] for i in range(0, len(outputs), num_generations)] # Just need one valid sample per test question
        vsr = sum(all_vsr)/len(all_vsr)
        print("Finished VSR computation.")
        
        # Compute IoU for all the generated STEPs
        steps = sorted(os.listdir(step_root)) # Sort steps alphabetically
        ground_truth_steps = ['/orcd/compute/faez/001/annie/DeepCAD/data/steps/' + i.split("_")[0][0:4] + "/" + i.split("_")[0] + ".step" for i in steps]
        generated_steps = [step_root + "/" + i for i in steps]
        
        tasks = list(zip(ground_truth_steps, generated_steps))
        print("Starting IoU computation...")
        with parallel_backend("multiprocessing"): #TODO: can get rid of this?
            with tqdm_joblib(tqdm(desc="Computing IoU", total=len(tasks))) as progress_bar:
                all_ious = Parallel(n_jobs=min(self.n_parallel // 2, len(tasks)))(
                    delayed(compute_iou)(gt, mg) for gt, mg in tasks
                )
        print("Finished IoU computation.")

        if len(all_ious) != len(steps):
            raise ValueError("length mismatch")
        
        # Group IoUs by identifier, compute max IoU per question
        # TODO: different identifier logic needed for differnet dataset?
        grouped_ious = defaultdict(list)
        for name, iou in zip(steps, all_ious):
            identifier = name.split("_")[0]
            grouped_ious[identifier].append(iou)
        max_ious = {k: max(v) for k, v in grouped_ious.items()}

        # Compute average of max IOUs
        average_max_iou = sum(max_ious.values()) / len(max_ious)

        # Write all IoUs to a file
        with open(f"{self.individual_experiment_path}/all_ious.txt", "w") as f:
            for identifier, max_iou in max_ious.items():
                f.write(f"{identifier} {max_iou:.6f}\n")
                
        shutil.rmtree(step_root) # Delete generated steps once computation done, TODO: could make this as argument
        return vsr, average_max_iou