import torch
from model_rag import SimpleRAGModel

def train():
    model = SimpleRAGModel()
    model.train_model("/data/processed/")
    print("✅ Training complete.")

if __name__ == "__main__":
    train()
