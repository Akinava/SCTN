FROM python:3-alpine
WORKDIR /usr/src/app

# copy app
COPY src/ .
COPY requirements.txt .

# install lib
RUN apk add g++
RUN wget https://raw.githubusercontent.com/Akinava/PyCrypto/master/src/pycrypto.py
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "./server.py"]