import io
import os
import sys
import zipfile
import boto3
import requests
from kaggle.api.kaggle_api_extended import KaggleApi

S3_BUCKET = "aegis-cic-training-2026-model.v1"
S3_PREFIX = "datasets/tabular-iot-attack-2024/raw/"

def stream_dataset_to_s3(dataset_slug):
    print("Authenticating with Kaggle...")
    api = KaggleApi()
    api.authenticate()

    owner, dataset_name = dataset_slug.split("/")
    url = f"https://www.kaggle.com/api/v1/datasets/download/{owner}/{dataset_name}"
    
    print(f"Connecting to stream: {dataset_slug}...")
    headers = {"Authorization": f"Bearer {api.config_values['key']}"} if "key" in api.config_values else {}
    auth = (api.config_values["username"], api.config_values["key"]) if "username" in api.config_values else None

    s3 = boto3.client("s3")
    
    with requests.get(url, headers=headers, auth=auth, stream=True) as resp:
        if resp.status_code != 200:
            print(f"Failed to fetch dataset: HTTP {resp.status_code} - {resp.text}")
            sys.exit(1)
            
        print("Connected! Reading compressed archive in-flight...")
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            file_list = [f for f in z.namelist() if not f.endswith("/")]
            print(f"Archive contains {len(file_list)} files.")

            for i, fname in enumerate(file_list, 1):
                clean_name = os.path.basename(fname)
                if not clean_name:
                    continue
                target_key = f"{S3_PREFIX}{clean_name}"
                print(f"[{i}/{len(file_list)}] Streaming {clean_name} -> s3://{S3_BUCKET}/{target_key}")
                with z.open(fname) as file_obj:
                    s3.upload_fileobj(file_obj, S3_BUCKET, target_key)

    print("\nCIC-BCCC-NRC TabularIoTAttack-2024 successfully ingested into S3!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 src/stream_tabular_iot_to_s3.py <dataset_slug>")
        sys.exit(1)
    stream_dataset_to_s3(sys.argv[1])
