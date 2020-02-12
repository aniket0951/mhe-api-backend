import requests

url = "https://172.16.241.227:789/Common.svc/SyncService"

payload = "<SyncRequestParam>\n\t<SyncLocationCode>MHN</SyncLocationCode>\n\t<SyncMethod>department</SyncMethod>\n</SyncRequestParam>"
headers = {
    'Content-Type': "application/xml",
    'User-Agent': "PostmanRuntime/7.20.1",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Postman-Token': "ae2a7d2d-e336-42c9-bf7a-7ab07fea24b0,284a7ef2-7054-4b8b-a8b3-4f19be2f3ca2",
    'Host': "172.16.241.227:789",
    'Accept-Encoding': "gzip, deflate",
    'Content-Length': "117",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
    }

response = requests.request("POST", url, data=payload, headers=headers)

print(response.text)