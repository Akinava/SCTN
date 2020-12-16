FROM python:3-alpine
WORKDIR /usr/src/app
COPY src/client.py .
COPY requirements.txt .
RUN pip install -qr requirements.txt
CMD ["python3", "./client.py"]