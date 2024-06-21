# syntax=docker/dockerfile:1

FROM python:3.9
WORKDIR /app
COPY . .
RUN MKDIR /app/downloads
RUN pip install -r requirements.txt
CMD ["python3", "app.py"]
