FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install torch transformers scikit-learn
CMD ["bash", "docker-shell.sh"]

