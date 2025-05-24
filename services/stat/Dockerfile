FROM python:3.11-slim

WORKDIR /stat

COPY services/stat/ .

COPY services/stat/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/stat/app:$PYTHONPATH"
COPY proto/stat.proto .
RUN python -m grpc_tools.protoc \
     -I. \
     --python_out=app \
     --grpc_python_out=app \
     stat.proto

EXPOSE 7000

CMD ["python", "main.py"]

