import boto3
import os
from tqdm import tqdm
import sys

def get_s3_objects(bucket, prefix):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    objects = []
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                objects.append(obj)
    return objects

def download_file(s3, bucket, key, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as f:
        s3.download_fileobj(bucket, key, f)

def download_with_progress(s3, bucket, objects, local_directory):
    total_size = sum(obj['Size'] for obj in objects)
    total_files = len(objects)
    failed_downloads = []

    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Gesamtfortschritt") as pbar:
        for obj in objects:
            key = obj['Key']
            file_size = obj['Size']
            local_path = os.path.join(local_directory, key)
            try:
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(key)) as file_pbar:
                    def callback(bytes_amount):
                        file_pbar.update(bytes_amount)
                        pbar.update(bytes_amount)

                    s3.download_file(bucket, key, local_path, Callback=callback)
            except Exception as e:
                print(f"Fehler beim Herunterladen von {key}: {e}")
                failed_downloads.append(key)

    return failed_downloads

def main(bucket_name, s3_directory, local_directory):
    s3 = boto3.client('s3')
    print(f"Lade Dateien aus s3://{bucket_name}/{s3_directory} in das lokale Verzeichnis {local_directory} herunter...")

    objects = get_s3_objects(bucket_name, s3_directory)
    total_files = len(objects)
    total_size = sum(obj['Size'] for obj in objects)
    print(f"Zu herunterladende Dateien: {total_files}")
    print(f"Gesamtgröße: {total_size / (1024*1024):.2f} MB")

    failed_downloads = download_with_progress(s3, bucket_name, objects, local_directory)

    print("\nZusammenfassung des Herunterladeprozesses:")
    print(f"Erfolgreich heruntergeladene Dateien: {total_files - len(failed_downloads)}")
    print(f"Fehlgeschlagene Downloads: {len(failed_downloads)}")
    if failed_downloads:
        print("Fehlgeschlagene Downloads:")
        for key in failed_downloads:
            print(f"- {key}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <bucket-name> <s3-directory> <local-directory>")
    else:
        bucket_name = sys.argv[1]
        s3_directory = sys.argv[2]
        local_directory = sys.argv[3]
        main(bucket_name, s3_directory, local_directory)
