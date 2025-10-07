FROM python:3.11-slim
WORKDIR /app
COPY Pipfile Pipfile.lock /app/
RUN pip install pipenv && pipenv install --system --deploy
COPY . /app
CMD ["bash", "docker-shell.sh"]

