import pandas as pd
import os

def load_data():
    raw_path = "/data/raw/dataset.csv"
    if not os.path.exists(raw_path):
        df = pd.read_csv("https://example.com/dataset.csv")
        os.makedirs("/data/raw", exist_ok=True)
        df.to_csv(raw_path, index=False)
    return raw_path

if __name__ == "__main__":
    print("✅ Data loaded:", load_data())
