FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY abi.py config.py eth-spider.py .
CMD ["python", "eth-spider.py"]
