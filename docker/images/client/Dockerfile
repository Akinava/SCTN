FROM python:3-alpine
RUN /usr/local/bin/python -m pip install --upgrade pip
WORKDIR /usr/src/app
COPY src/ .
COPY docker/images/server/requirements.txt .
RUN pip install -qr requirements.txt
CMD ["python3", "./client.py"]