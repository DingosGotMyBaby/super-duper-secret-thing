FROM python:3.10-bookworm

RUN apt-get update
RUN apt-get install -y build-essential
RUN pip install --upgrade pip


WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY models.py .

CMD [ "python3", "app.py" ]