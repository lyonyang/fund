FROM python:3.6.3

MAINTAINER Lyon Yang

WORKDIR /fund

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 80 8000

CMD  ["python", "./run.py", "--port=8000"]