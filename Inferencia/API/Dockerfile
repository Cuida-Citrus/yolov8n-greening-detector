FROM python:3.12-slim

# 1) instala as deps de sistema que o cv2/ultralytics precisa
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libgl1 \
      libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 2) define diretório de trabalho
WORKDIR /app

# 3) copia requirements e instala
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 4) copia o seu código
COPY app ./app

# 5) expõe a porta e define comando de startup
ENV PORT=80
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
