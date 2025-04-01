FROM python:3.11-slim

WORKDIR /post

COPY services/post/ .

COPY services/post/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/post/app:$PYTHONPATH"
COPY proto/post.proto .
RUN python -m grpc_tools.protoc \
     -I. \
     --python_out=app \
     --grpc_python_out=app \
     post.proto

EXPOSE 6000

CMD ["python", "main.py"]

