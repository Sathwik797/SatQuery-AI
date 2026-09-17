import urllib.request
import json

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
file_path = 'data/external_datasets/rsvqa/images/rsvqa_lr_0000.png'
with open(file_path, 'rb') as f:
    file_bytes = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="rsvqa_lr_0000.png"\r\n'
    f'Content-Type: image/png\r\n\r\n'
).encode('utf-8') + file_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
print(f"Upload Success: {res['id']} ({res['filename']}, {res['metadata']['width']}x{res['metadata']['height']})")

# Query the freshly uploaded image
query_data = json.dumps({
    'primary_id': res['id'],
    'secondary_id': None,
    'query': 'Is this area mostly urban or rural?',
    'conversation_id': 'upload-test'
}).encode('utf-8')

q_req = urllib.request.Request('http://127.0.0.1:8000/api/analyze', data=query_data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(q_req) as q_resp:
    q_res = json.loads(q_resp.read().decode('utf-8'))
print(f"Query on Uploaded Image Success: {q_res['answer']} (Confidence: {q_res['confidence']}, Task: {q_res['task']})")
