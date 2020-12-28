FROM python:3-alpine
WORKDIR /usr/src/app

# install lib
COPY requirements.txt .
RUN apk add g++
RUN wget https://raw.githubusercontent.com/Akinava/PyCrypto/master/src/pycrypto.py
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app
COPY src/ .
COPY test/ .

CMD ["python3", "test_peer.py"]
