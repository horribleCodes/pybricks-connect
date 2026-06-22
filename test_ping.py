import requests

HOST = "127.0.0.1"
PORT = 5000

url = f"http://{HOST}:{PORT}/ping"
data = {"key": "value"}

print("Pinging ", url)
response = requests.post(url, json=data)

print(response.text)
