FROM python:3.10-slim-buster AS pws-base
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN python setup.py install