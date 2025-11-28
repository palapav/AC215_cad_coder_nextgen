import json
import os
from tqdm.auto import trange
from PIL import Image

def load_images(data):
    images = []
    for i in trange(len(data)):
        image_path = data[i]['prompt'][1]['content'][0]['image']
        image = Image.open(image_path).convert('RGB')
        images.append(image)
    return images

def load_jsonl_with_json(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                json_object = json.loads(line)
                data.append(json_object)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON: {line.strip()} due to error: {e}")
    return data

def convert_from_old_format(old_data_path, base_path,
                            system_message="You are a helpful assistant.",
                            remove_from_prompt=" Just the code, no other words.",
                            add_insruct_like_reponse=True,
                            pre_load_images=False):
    
    if '.jsonl' not in old_data_path:
        data = json.load(open(old_data_path, "r"))
    else:
        data = load_jsonl_with_json(old_data_path)
        
    new_data = []

    for i in trange(len(data)):
        
        if not add_insruct_like_reponse:
            assistant_response = data[i]['conversations'][1]['value']
        else:
            assistant_response = "Certainly! Based on the provided image, here is the CADQuery code to generate the corresponding CAD model:\n```python\n" + data[i]['conversations'][1]['value'] + "```\n\nThe variable `solid` contains the final CAD model. You can use it to export the model in various formats, such as STEP or STL, using the appropriate methods in the CADQuery library.\n\nIf you have any other questions or would like to modify the model further, feel free to ask!\n\n"
        
        d = {
            "id": data[i]['id'],
            "Type": "Instruct",
            "MM": True,
            "prompt": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": system_message
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": os.path.join(base_path, data[i]['image'])
                        },
                        {
                            "type": "text",
                            "text": data[i]['conversations'][0]['value'].replace("<image>\n", "").replace(remove_from_prompt, "")
                        },
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": assistant_response
                        }
                    ]
                }
            ]
        }
        
        new_data.append(d)
    
    if pre_load_images:
        images = load_images(new_data)
        for i in trange(len(new_data), desc="Loading images"):
            new_data[i]['prompt'][1]['content'][0]['image'] = images[i]
    
    return new_data

