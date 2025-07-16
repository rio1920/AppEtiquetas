FROM python:3.13.5-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .



# se eejcuta cuando la imagen se inicia en un contenedor
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

# crear imagen -----docker build --tag labelary:latest . ---el punto es el path relativo al dockerfile
# en caso de volver a ejecutar el comando  con otro tag apuntara a la misma imagen
# renombrar la imagen con el comando -- docker image tag labelary:latest labelary:v1.0

# para subir una imagen a docker hub se usa el comando
# primero se debe hacer login con el comando
# docker login --username=tu_usuario --password=tu_contraseña
# luego se sube la imagen con el comando
# luego crear el repositorio en docker hub con el nombre de la imagen
# docker push tu_usuario/labelary:latest
# si el repositorio es privado se debe usar el comando
# docker push labelary:latest