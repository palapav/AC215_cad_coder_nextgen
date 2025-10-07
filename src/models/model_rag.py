from transformers import AutoModelForCausalLM, AutoTokenizer

class SimpleRAGModel:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B")
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B")

    def train_model(self, data_path):
        # fine-tuning logic here
        print("Training on:", data_path)
