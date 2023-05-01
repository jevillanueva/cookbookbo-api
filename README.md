# Cocina boliviana

## Desarrollo

Para iniciar configurar el archivo .env usando .env.production, desde visual code puede ejecutar con F5 donde se cargara las variables de entorno del archivo .env y se ejecutará el siguiente comando, puede revisar esto en el archivo .vscode/launch.json con el nombre: "Python: Uvicorn"

```py
uvicorn app.main:app --host 0.0.0.0  --reload
```


## Producción

Para producción conn Kubernetes se tienen en la carpeta k8s los archivos básicos para su deployment, el caso de secrets se tiene que crear de acuerdo a las variables .env donde la plantilla esta en .env.production y el secret para almacenar el archivo json de la cuenta de servicio para gcp storage.

```bash
kubectl create secret generic cookbookbo-api-gcp-storage --from-file=.\keys\sample.json
kubectl create secret generic cookbookbo-api --from-env-file=.env

```

Levantar el deployment

```bash
kubectl create -f deploy.yaml
```

Para levantar el servicio

```bash
kubectl create -f service.yaml
```

Para levantar la exposicion mediante la ip del server se puede usar usando el explose.yml o el ingress.yaml que ya incluye configuracion de dominio.

```bash
kubect create -f ingress.yaml
#o  
kubect create -f expose.yaml
```
