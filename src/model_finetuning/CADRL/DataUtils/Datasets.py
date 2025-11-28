from PIL import Image
import json
import numpy as np
from tqdm.auto import trange
import torch
import torchvision
from typing import Optional, Tuple, List, Dict, Any, Union, Callable
import pickle
import io
from copy import deepcopy
from datasets import Dataset
import joblib
import base64
from io import BytesIO
import asyncio
import re

def extract_code(text):
    # Use regex to find the code block
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return text
    
class CADLMDataset(torch.utils.data.Dataset):
    def __init__(self, 
                 data_dict: Union[str, List[dict], Dataset],
                 collate_fn: Callable,
                 pre_load_vision: bool = True,
                 num_workers: int = 1,
                 image_augmentation_fn: Optional[Callable] = None,
                 basic_image_augmentation: bool = False,
                 augmentation_probability: float = 0.5
                 ):
        """
        Args:
            data_dict (Union[str, Dict[Any]]): Path to the jsonl file or a dictionary containing the dataset or pickle file with image objects.
            collate_fn (Callable): Function to collate the data. (input will be messages in a given sample same as the template in CADLM)
            pre_load_vision (bool, optional): Whether to pre-load vision data. Defaults to True.
        """
        super().__init__()
        if isinstance(data_dict, str):
            if data_dict.endswith('.jsonl'):
                self.data_dict = self._read_jsonl_with_json(data_dict)
            elif data_dict.endswith('.pkl'):
                with open(data_dict, 'rb') as f:
                    self.data_dict = pickle.load(f)
                if not isinstance(self.data_dict, list):
                    raise ValueError("Pickle file must contain a list of dictionaries.")
            else:
                raise ValueError("Unsupported file format. Only .jsonl files are supported.")
        elif isinstance(data_dict, list):
            self.data_dict = data_dict
        elif isinstance(data_dict, Dataset):
            self.data_dict = data_dict
        else:
            raise ValueError("data_dict must be a path to a .jsonl file or a list of dictionaries.")
        
        self.pre_load_vision = pre_load_vision
        self._collate_fn = collate_fn
        self.num_workers = num_workers
        
        if image_augmentation_fn is not None:
            self.image_augmentation_fn = image_augmentation_fn
        elif basic_image_augmentation:
            self.image_augmentation_fn = torchvision.transforms.Compose([
                torchvision.transforms.RandomHorizontalFlip(),
                torchvision.transforms.RandomVerticalFlip(),
                torchvision.transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                torchvision.transforms.RandomErasing(p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)),
                torchvision.transforms.RandomAffine(degrees=45, translate=(0.2, 0.2), scale=(0.75, 1.25))
            ])
        else:
            self.image_augmentation_fn = None
            
        self.augmentation_probability = augmentation_probability
        
        self._validate_data()
    
    def _validate(self, sample, i):
        if 'Type' not in sample:
            sample['Type'] = 'Instruct' # Default to 'Instruct' if not present
        else:
            if sample['Type'] not in ['Pretraining', 'Instruct', 'RL']:
                raise ValueError(f"Invalid Type: {sample['Type']}. Expected 'Pretraining', 'Instruct', or 'RL'.")
            if sample['Type'] == 'RL':
                raise ValueError(f"RL type is not supported yet. Sample {i} has RL type.")
        if 'MM' not in sample:
            sample['MM'] = False # Default to False if not present
        elif not isinstance(sample['MM'], bool):
            raise ValueError(f"Invalid MM: {sample['MM']}. Expected a boolean value.")
        
        if "prompt" not in sample:
            raise ValueError(f"Missing 'prompt' key in sample {i}.")
        else:
            if sample['Type'] == 'Pretraining' and len(sample["prompt"]) != 1:
                raise ValueError(f"Pretraining samples should have exactly one prompt. Sample {i} has {len(sample['prompt'])} prompts.")
            for j in range(len(sample["prompt"])):
                if sample['Type'] == 'Instruct':
                    if 'role' not in sample["prompt"][j]:
                        raise ValueError(f"Missing 'role' key in prompt {j} of sample {i}.")
                    elif sample["prompt"][j]['role'] not in ['user', 'assistant', 'system']:
                        raise ValueError(f"Invalid role: {sample['prompt'][j]['role']}. Expected 'user', 'assistant', or 'system'.")
                
                if "content" not in sample["prompt"][j]:
                    raise ValueError(f"Missing 'content' key in prompt {j} of sample {i}.")
                else:
                    for k in range(len(sample["prompt"][j]["content"])):
                        if 'type' not in sample["prompt"][j]["content"][k]:
                            raise ValueError(f"Missing 'type' key in content {k} of prompt {j} in sample {i}.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'text':
                            if 'text' not in sample["prompt"][j]["content"][k]:
                                raise ValueError(f"Missing 'text' key in content {k} of prompt {j} in sample {i}.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'image':
                            if not sample['MM']:
                                sample['MM'] = True
                    
                            if 'image' not in sample["prompt"][j]["content"][k]:
                                raise ValueError(f"Missing 'image' key in content {k} of prompt {j} in sample {i}.")
                            else:
                                if isinstance(sample["prompt"][j]["content"][k]['image'], str) and self.pre_load_vision:
                                    image_path = sample["prompt"][j]["content"][k]['image']
                                    # load the image with PIL
                                    try:
                                        if 'variant' not in  sample["prompt"][j]["content"][k]:
                                            image = Image.open(image_path).convert("RGB")
                                        elif sample["prompt"][j]["content"][k]['variant'] == 'RGBD':
                                            raise NotImplementedError("RGBD variant is not implemented yet.")
                                        else:
                                            image = Image.open(image_path).convert("RGB")
                                        
                                        sample["prompt"][j]["content"][k]['image'] = image
                                    except Exception as e:
                                        raise ValueError(f"Error loading image {image_path} in sample {i}: {e}")
                                elif isinstance(sample["prompt"][j]["content"][k]['image'], dict):
                                    # loaded from hf with bytes
                                    if 'bytes' not in sample["prompt"][j]["content"][k]['image']:
                                        raise ValueError(f"Missing 'bytes' key in image content {k} of prompt {j} in sample {i}.")
                                    
                                    bytes_data = sample["prompt"][j]["content"][k]['image']['bytes']
                                    buffer = io.BytesIO(bytes_data)
                                    try:
                                        if 'variant' not in sample["prompt"][j]["content"][k]:
                                            image = Image.open(buffer).convert("RGB")
                                        elif sample["prompt"][j]["content"][k]['variant'] == 'RGBD':
                                            raise NotImplementedError("RGBD variant is not implemented yet.")
                                        else:
                                            image = Image.open(buffer).convert("RGB")
                                            
                                        sample["prompt"][j]["content"][k]['image'] = image
                                    except Exception as e:
                                        raise ValueError(f"Error loading image in sample {i}: {e}")
                                    
                        elif sample["prompt"][j]["content"][k]['type'] == 'video':
                            raise NotImplementedError("Video type is not implemented yet.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'CAD':
                            raise NotImplementedError("CAD type is not implemented yet.")
                        elif sample["prompt"][j]["content"][k]['type'] == '3D':
                            raise NotImplementedError("3D type is not implemented yet.")
    @staticmethod
    def _validate_individual(sample, i, pre_load_vision=True):
        if 'Type' not in sample:
            sample['Type'] = 'Instruct' # Default to 'Instruct' if not present
        else:
            if sample['Type'] not in ['Pretraining', 'Instruct', 'RL']:
                raise ValueError(f"Invalid Type: {sample['Type']}. Expected 'Pretraining', 'Instruct', or 'RL'.")
            if sample['Type'] == 'RL':
                raise ValueError(f"RL type is not supported yet. Sample {i} has RL type.")
        if 'MM' not in sample:
            sample['MM'] = False # Default to False if not present
        elif not isinstance(sample['MM'], bool):
            raise ValueError(f"Invalid MM: {sample['MM']}. Expected a boolean value.")
        
        if "prompt" not in sample:
            raise ValueError(f"Missing 'prompt' key in sample {i}.")
        else:
            if sample['Type'] == 'Pretraining' and len(sample["prompt"]) != 1:
                raise ValueError(f"Pretraining samples should have exactly one prompt. Sample {i} has {len(sample['prompt'])} prompts.")
            for j in range(len(sample["prompt"])):
                if sample['Type'] == 'Instruct':
                    if 'role' not in sample["prompt"][j]:
                        raise ValueError(f"Missing 'role' key in prompt {j} of sample {i}.")
                    elif sample["prompt"][j]['role'] not in ['user', 'assistant', 'system']:
                        raise ValueError(f"Invalid role: {sample['prompt'][j]['role']}. Expected 'user', 'assistant', or 'system'.")
                
                if "content" not in sample["prompt"][j]:
                    raise ValueError(f"Missing 'content' key in prompt {j} of sample {i}.")
                else:
                    for k in range(len(sample["prompt"][j]["content"])):
                        if 'type' not in sample["prompt"][j]["content"][k]:
                            raise ValueError(f"Missing 'type' key in content {k} of prompt {j} in sample {i}.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'text':
                            if 'text' not in sample["prompt"][j]["content"][k]:
                                raise ValueError(f"Missing 'text' key in content {k} of prompt {j} in sample {i}.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'image':
                            if not sample['MM']:
                                sample['MM'] = True
                    
                            if 'image' not in sample["prompt"][j]["content"][k]:
                                raise ValueError(f"Missing 'image' key in content {k} of prompt {j} in sample {i}.")
                            else:
                                if isinstance(sample["prompt"][j]["content"][k]['image'], str) and pre_load_vision:
                                    image_path = sample["prompt"][j]["content"][k]['image']
                                    # load the image with PIL
                                    try:
                                        if 'variant' not in  sample["prompt"][j]["content"][k]:
                                            image = Image.open(image_path).convert("RGB")
                                        elif sample["prompt"][j]["content"][k]['variant'] == 'RGBD':
                                            raise NotImplementedError("RGBD variant is not implemented yet.")
                                        else:
                                            image = Image.open(image_path).convert("RGB")
                                        
                                        sample["prompt"][j]["content"][k]['image'] = image
                                    except Exception as e:
                                        raise ValueError(f"Error loading image {image_path} in sample {i}: {e}")
                                elif isinstance(sample["prompt"][j]["content"][k]['image'], dict):
                                    # loaded from hf with bytes
                                    if 'bytes' not in sample["prompt"][j]["content"][k]['image']:
                                        raise ValueError(f"Missing 'bytes' key in image content {k} of prompt {j} in sample {i}.")
                                    
                                    bytes_data = sample["prompt"][j]["content"][k]['image']['bytes']
                                    buffer = io.BytesIO(bytes_data)
                                    try:
                                        if 'variant' not in sample["prompt"][j]["content"][k]:
                                            image = Image.open(buffer).convert("RGB")
                                        elif sample["prompt"][j]["content"][k]['variant'] == 'RGBD':
                                            raise NotImplementedError("RGBD variant is not implemented yet.")
                                        else:
                                            image = Image.open(buffer).convert("RGB")
                                            
                                        sample["prompt"][j]["content"][k]['image'] = image
                                    except Exception as e:
                                        raise ValueError(f"Error loading image in sample {i}: {e}")
                                    
                        elif sample["prompt"][j]["content"][k]['type'] == 'video':
                            raise NotImplementedError("Video type is not implemented yet.")
                        elif sample["prompt"][j]["content"][k]['type'] == 'CAD':
                            raise NotImplementedError("CAD type is not implemented yet.")
                        elif sample["prompt"][j]["content"][k]['type'] == '3D':
                            raise NotImplementedError("3D type is not implemented yet.")
                        
        return sample
    
    def _validate_data(self):
        print("Validating data...")
        if self.num_workers > 1:
            with joblib.Parallel(n_jobs=self.num_workers) as parallel:
                self.data_dict = parallel(joblib.delayed(self._validate_individual)(self.data_dict[i], i, self.pre_load_vision) for i in trange(len(self.data_dict), desc="Validating data"))
        else:
            for i in trange(len(self.data_dict), desc="Validating data"):
                sample = self.data_dict[i]
                self._validate(sample, i)


    def __len__(self):
        return len(self.data_dict)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        
        sample = deepcopy(self.data_dict[idx])

        if sample['MM'] and not self.pre_load_vision:
            for j in range(len(sample["prompt"])):
                for k in range(len(sample["prompt"][j]["content"])):
                    if sample["prompt"][j]["content"][k]['type'] == 'image':
                        if isinstance(sample["prompt"][j]["content"][k]['image'], str):
                            image_path = sample["prompt"][j]["content"][k]['image']
                            try:
                                if 'variant' not in  sample["prompt"][j]["content"][k]:
                                    image = Image.open(image_path).convert("RGB")
                                elif sample["prompt"][j]["content"][k]['variant'] == 'RGBD':
                                    raise NotImplementedError("RGBD variant is not implemented yet.")
                                else:
                                    image = Image.open(image_path).convert("RGB")

                                sample["prompt"][j]["content"][k]['image'] = image
                            except Exception as e:
                                raise ValueError(f"Error loading image {image_path} in sample {idx}: {e}")

        if self.image_augmentation_fn is not None and sample['MM'] and np.random.rand() < self.augmentation_probability:
            for j in range(len(sample["prompt"])):
                for k in range(len(sample["prompt"][j]["content"])):
                    if sample["prompt"][j]["content"][k]['type'] == 'image':
                        image = sample["prompt"][j]["content"][k]['image']
                        if isinstance(image, Image.Image):
                            image_tensor = torchvision.transforms.ToTensor()(image)
                            augmented_image_tensor = self.image_augmentation_fn(image_tensor)
                            new_image = torchvision.transforms.ToPILImage()(augmented_image_tensor)
                            sample["prompt"][j]["content"][k]['image'] = new_image

        # remove any text or image with None
        for j in range(len(sample["prompt"])):
            for k in range(len(sample["prompt"][j]["content"])):
                for key in list(sample["prompt"][j]["content"][k].keys()):
                    if sample["prompt"][j]["content"][k][key] is None:
                        sample["prompt"][j]["content"][k].pop(key)
                        
        return sample["prompt"]
    
    @staticmethod
    def _read_jsonl_with_json(file_path):
        data = []
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    json_object = json.loads(line)
                    data.append(json_object)
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON: {line.strip()} due to error: {e}")
        return data
    
    @staticmethod
    def encode_image(image: Image.Image, im_type='jpeg') -> str:
        buffered = BytesIO()
        image.save(buffered, format=im_type)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def _vllm_processor(self, i, image_type):
        prompt = self[i]
        # remove assistant role if present
        for j in range(len(prompt)):
            if prompt[j]['role'] == 'assistant':
                gt = prompt[j]['content'][0]['text']
                prompt.pop(j)
                continue
            for k in range(len(prompt[j]['content'])):
                if prompt[j]['content'][k]['type'] == 'image':
                    prompt[j]['content'][k]['type'] = 'image_url'
                    im = prompt[j]['content'][k]['image']
                    im_encoded = self.encode_image(im, im_type=image_type)
                    im_encoded = f"data:image/{image_type};base64,{im_encoded}"
                    prompt[j]['content'][k].pop('image')
                    prompt[j]['content'][k]['image_url'] = {'url': im_encoded}
        
        return prompt, gt
    
    def gather_vllm_data(self, image_type='png'):
        prompts = []
        gt = []
        for i in trange(len(self), desc="Preparing prompts for VLLM"):
            prompt = self[i]
            
            # remove assitant role if present
            for j in range(len(prompt)):
                if prompt[j]['role'] == 'assistant':
                    gt.append(prompt[j]['content'][0]['text'])
                    prompt.pop(j)
                    continue
                for k in range(len(prompt[j]['content'])):
                    if prompt[j]['content'][k]['type'] == 'image':
                        prompt[j]['content'][k]['type'] = 'image_url'
                        im = prompt[j]['content'][k]['image']
                        im_encoded = self.encode_image(im, im_type=image_type)
                        im_encoded = f"data:image/{image_type};base64,{im_encoded}"
                        prompt[j]['content'][k].pop('image')
                        prompt[j]['content'][k]['image_url'] = {'url': im_encoded}

            prompts.append(prompt)
        return prompts, gt
    
    def gather_vllm_data_parallel(self, image_type='png', n_workers: Optional[int] = 16):
        from joblib import Parallel, delayed
        prompts = []
        gt = []
        
        def process_sample(i):
            return self._vllm_processor(i, image_type)
        
        results = Parallel(n_jobs=n_workers)(delayed(process_sample)(i) for i in trange(len(self), desc="Preparing prompts for VLLM"))
        
        for prompt, gt_text in results:
            prompts.append(prompt)
            gt.append(gt_text)
        
        return prompts, gt
        
                    
class MinimalImageCADDataset(torch.utils.data.Dataset):
    def __init__(self, 
                 data_dict: List[dict],
                 collate_fn: Callable,
                 system_prompt: Optional[str] = "You are a helpful assistant.",
                 user_prompt: Optional[str] = "Generate the CADQuery code needed to create the CAD for the provided image.",
                 assistant_response_template: Optional[str] = "Certainly! Based on the provided image, here is the CADQuery code to generate the corresponding CAD model:\n```python\n{code}\n```\n\nThe variable `solid` contains the final CAD model. You can use it to export the model in various formats, such as STEP or STL, using the appropriate methods in the CADQuery library.\n\nIf you have any other questions or would like to modify the model further, feel free to ask!",
                 image_augmentation_fn: Optional[Callable] = None,
                 basic_image_augmentation: bool = False,
                 augmentation_probability: float = 0.5,
                 pc_input: bool = False,
                 image_input: bool = True,
                 pc_user_prompt: Optional[str] = "Generate the CADQuery code needed to create the CAD for the provided image and point cloud data.",
                 pc_assistant_response_template: Optional[str] = "Certainly! Based on the provided image and point cloud data, here is the CADQuery code to generate the corresponding CAD model:\n```python\n{code}\n```\n\nThe variable `solid` contains the final CAD model. You can use it to export the model in various formats, such as STEP or STL, using the appropriate methods in the CADQuery library.\n\nIf you have any other questions or would like to modify the model further, feel free to ask!",
                 num_points: int = 256):
        """
        Args:
            data_dict (List[dict]): List of dictionaries containing the dataset.
            collate_fn (Callable): Function to collate the data. (input will be messages in a given sample same as the template in CADLM)
            image_augmentation_fn (Optional[Callable], optional): Function for image augmentation. Defaults to None.
            basic_image_augmentation (bool, optional): Whether to apply basic image augmentation. Defaults to False.
            augmentation_probability (float, optional): Probability of applying augmentation. Defaults to 0.5.
        """
        super().__init__()
        
        self.data_dict = data_dict
        self._collate_fn = collate_fn
        if image_augmentation_fn is not None:
            self.image_augmentation_fn = image_augmentation_fn
        elif basic_image_augmentation:
            self.image_augmentation_fn = torchvision.transforms.Compose([
                torchvision.transforms.RandomHorizontalFlip(),
                torchvision.transforms.RandomVerticalFlip(),
                torchvision.transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                torchvision.transforms.RandomErasing(p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)),
                torchvision.transforms.RandomAffine(degrees=45, translate=(0.2, 0.2), scale=(0.75, 1.25))
            ])
        else:
            self.image_augmentation_fn = None
        self.augmentation_probability = augmentation_probability
        
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.assistant_response_template = assistant_response_template
        self.pc_user_prompt = pc_user_prompt
        self.pc_assistant_response_template = pc_assistant_response_template
        self.pc_input = pc_input
        self.image_input = image_input
        self.num_points = num_points

    def __len__(self):
        return len(self.data_dict)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        image = self.data_dict[idx]['image']
        code = self.data_dict[idx]['code']
        
        # Apply image augmentation if specified
        if self.image_augmentation_fn is not None and np.random.rand() < self.augmentation_probability:
            if isinstance(image, Image.Image):
                image_tensor = torchvision.transforms.ToTensor()(image)
                augmented_image_tensor = self.image_augmentation_fn(image_tensor)
                image = torchvision.transforms.ToPILImage()(augmented_image_tensor)

        # Set up point cloud tokens
        if self.pc_input:
            pc_tokens = "".join(["<pc>"] * self.num_points)
            # system_prompt = f"{pc_tokens}\n{self.system_prompt}"
            user_prompt = f"{pc_tokens}\n{self.pc_user_prompt}"
            assistant_template = self.pc_assistant_response_template
        else:
            user_prompt = self.user_prompt
            assistant_template = self.assistant_response_template

        # PC with no image
        if not self.image_input:
            # Order is sysmte prompt, beginning of user prompt "user", image, point clouds, query of user prompt
            prompt = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": assistant_template.format(code=code)}]
                }
            ]
        else: # PC with image
            prompt = [
            {
                "role": "system",
                "content": [{"type": "text", "text": self.system_prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "image", "image": image},
                            {"type": "text", "text": user_prompt}]
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": assistant_template.format(code=code)}]
            }
        ]
        
        # Return prompt with pc if it exists
        result = {"prompt": prompt}
        if self.pc_input:
            result["pc"] = self.data_dict[idx]['pc']
            result["has_pc"] = True
        else:
            # print("COLALTOR: DOES NOT HAVE PC")
            result["has_pc"] = False

        return result
    
    @staticmethod
    def encode_image(image: Image.Image, im_type='jpeg') -> str:
        buffered = BytesIO()
        image.save(buffered, format=im_type)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def gather_vllm_data(self, image_type='png'):
        prompts = []
        gt = []
        for idx in trange(len(self.data_dict)):
            image = self.data_dict[idx]['image']
            code = self.data_dict[idx]['code']
            
            prompt = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/{image_type};base64,{self.encode_image(image, im_type=image_type)}"}},
                                {"type": "text", "text": self.user_prompt}]
                }
            ]
            prompts.append(prompt)
            gt.append(code)
    
        return prompts, gt

    
class CADRLDataset(torch.utils.data.Dataset):
    def __init__(self, 
                 data_dict: List[dict],
                 collate_fn: Callable,
                 system_prompt: Optional[str] = "You are a helpful assistant.",
                 user_prompt: Optional[str] = "Generate the CADQuery code needed to create the CAD for the provided image.",
                 assistant_response_template: Optional[str] = "Certainly! Based on the provided image, here is the CADQuery code to generate the corresponding CAD model:\n```python\n{code}\n```\n\nThe variable `solid` contains the final CAD model. You can use it to export the model in various formats, such as STEP or STL, using the appropriate methods in the CADQuery library.\n\nIf you have any other questions or would like to modify the model further, feel free to ask!",
                 image_augmentation_fn: Optional[Callable] = None,
                 basic_image_augmentation: bool = False,
                 augmentation_probability: float = 0.5,
                 image_type: str = 'png'
                 ):
        """
        Args:
            data_dict (List[dict]): List of dictionaries containing the dataset.
            collate_fn (Callable): Function to collate the data. (input will be messages in a given sample same as the template in CADLM)
            image_augmentation_fn (Optional[Callable], optional): Function for image augmentation. Defaults to None.
            basic_image_augmentation (bool, optional): Whether to apply basic image augmentation. Defaults to False.
            augmentation_probability (float, optional): Probability of applying augmentation. Defaults to 0.5.
        """
        super().__init__()
        
        self.data_dict = data_dict
        self._collate_fn = collate_fn
        if image_augmentation_fn is not None:
            self.image_augmentation_fn = image_augmentation_fn
        elif basic_image_augmentation:
            self.image_augmentation_fn = torchvision.transforms.Compose([
                torchvision.transforms.RandomHorizontalFlip(),
                torchvision.transforms.RandomVerticalFlip(),
                torchvision.transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                torchvision.transforms.RandomErasing(p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)),
                torchvision.transforms.RandomAffine(degrees=45, translate=(0.2, 0.2), scale=(0.75, 1.25))
            ])
        else:
            self.image_augmentation_fn = None
        self.augmentation_probability = augmentation_probability
        
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.assistant_response_template = assistant_response_template
        self.image_type = image_type
        
    def __len__(self):
        return len(self.data_dict)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        image = self.data_dict[idx]['image']
        code = self.data_dict[idx]['code']
        
        if self.image_augmentation_fn is not None and np.random.rand() < self.augmentation_probability:
            if isinstance(image, Image.Image):
                image_tensor = torchvision.transforms.ToTensor()(image)
                augmented_image_tensor = self.image_augmentation_fn(image_tensor)
                image = torchvision.transforms.ToPILImage()(augmented_image_tensor)
                
        vllm_prompt = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/{self.image_type};base64,{self.encode_image(image, im_type=self.image_type)}"}},
                                {"type": "text", "text": self.user_prompt}]
                }
            ]
        
        return {"image": image, "code": code, "vllm_prompt": vllm_prompt}

    @staticmethod
    def encode_image(image: Image.Image, im_type='jpeg') -> str:
        buffered = BytesIO()
        image.save(buffered, format=im_type)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def gather_vllm_data(self, image_type='png'):
        prompts = []
        gt = []
        for idx in trange(len(self.data_dict)):
            image = self.data_dict[idx]['image']
            code = self.data_dict[idx]['code']
            
            prompt = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/{image_type};base64,{self.encode_image(image, im_type=image_type)}"}},
                                {"type": "text", "text": self.user_prompt}]
                }
            ]
            prompts.append(prompt)
            gt.append(code)
    
        return prompts, gt
