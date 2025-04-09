FROM python:3.11-slim

WORKDIR /api-gateway

COPY services/api-gateway/ .

COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/api-gateway/app:$PYTHONPATH"
COPY proto/post.proto .
RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=app \
    --grpc_python_out=app \
    post.proto

EXPOSE 8000
CMD ["python", "main.py"]
