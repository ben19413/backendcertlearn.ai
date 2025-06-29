FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt ./
RUN apt-get update && \
    apt-get install -y gcc g++ gnupg2 curl && \
    apt-get remove -y unixodbc unixodbc-dev odbcinst odbcinst1debian2 libodbc1 libodbcinst2 || true && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
COPY ./data ./data
CMD ["uvicorn", "--app-dir", "app", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]
