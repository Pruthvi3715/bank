import requests
import time

print("Starting request...")
start_time = time.time()
try:
    r = requests.post("http://127.0.0.1:8000/api/run-pipeline")
    print(f"Status Code: {r.status_code}")
    print(f"Response (first 200 chars): {str(r.json())[:200]}")
    print(f"Elapsed Time: {time.time() - start_time:.2f}s")
except Exception as e:
    print(e)
