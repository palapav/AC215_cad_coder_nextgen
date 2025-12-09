#!/bin/bash

# Script to download training data from GCS to the data folder
# Make sure gsutil is installed and authenticated before running this script

cd "$(dirname "$0")"

gsutil -m cp \
  "gs://cad-coder-nextgen-data/raw_data/train/train_0.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_0.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_10.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_10.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_100.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_100.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1000.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1000.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1001.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1001.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1002.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1002.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1003.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1003.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1004.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1004.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1005.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1005.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1006.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1006.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1007.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1007.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1008.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1008.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1009.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1009.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_101.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_101.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1010.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1010.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1011.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1011.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1012.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1012.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1013.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1013.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1014.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1014.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1015.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1015.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1016.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1016.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1017.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1017.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1018.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1018.py" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1019.png" \
  "gs://cad-coder-nextgen-data/raw_data/train/train_1019.py" \
  .

echo "Download complete! Files saved to: $(pwd)"

