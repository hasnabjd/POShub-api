# POSHub API - Serverless FastAPI

FastAPI-based POS system API with external service integration.

### 1. Construire l'application
```bash
sam build --template sam-min.yml
```


# Tester la fonction Lambda localement
```bash
sam local invoke PosHubFunction --template sam-min.yml
```


## 📦 Déploiement

### Déploiement initial
```bash
sam deploy --template sam-min.yml --guided
```