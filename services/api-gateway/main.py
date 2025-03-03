import requests
from flask import Flask, request, Response
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user:5000/user")

@app.route('/user/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    url = f'{USER_SERVICE_URL}/{path}'
    
    headers = dict(request.headers)
    headers.pop('Host', None)

    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        json=request.get_json(),
        params=request.args
    )

    return Response(response.content, response.status_code, response.headers.items())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
