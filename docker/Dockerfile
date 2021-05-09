FROM python:3-alpine
WORKDIR /usr/src/app

# install lib
COPY requirements.txt .
RUN apk add g++
RUN apk add git
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app
COPY src/ .
COPY test/ .
COPY docker/config.json .
COPY docker/peers.json .

CMD ["python3", "test_peer.py"]
