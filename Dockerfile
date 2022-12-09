FROM python:3.8-slim-buster

COPY babynames-clean.csv /opt/app/
COPY requirements.txt /opt/app/

RUN pip install -r /opt/app/requirements.txt

COPY templates/index.html /opt/app/templates/index.html
COPY src/ /opt/app/

EXPOSE 5000

WORKDIR /opt/app
ENV FLASK_APP="api.py"

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]