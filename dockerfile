FROM python:3.8-slim-buster

# add work dir
WORKDIR /Weather_forecast

# Add all files in the current directory to docker image
COPY main.py requirements.txt ./

RUN pip install -r requirements.txt

#ENTRYPOINT ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]

ENTRYPOINT ["python", "main.py"]