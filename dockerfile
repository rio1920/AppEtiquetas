FROM python:3.13.5-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .



# se eejcuta cuando la imagen se inicia en un contenedor
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

# docker build --tag labelary:latest . el putn oes el path realativo al dockerfile
