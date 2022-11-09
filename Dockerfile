FROM python:3.10-alpine
LABEL MAINTAINER="Jonathan Villanueva <frik_ej2v@hotmail.com>"
WORKDIR /app/
ADD . /app/
RUN pip install  --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--workers", "2", "--host", "0.0.0.0" ]