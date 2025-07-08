# POSHub REST API - Gestion des Commandes avec SQS et DLQ



# 📋 CHAPITRE 5 - SQS & DLQ

> **🔄 Branche : `feature/dlq`**

## Lambda Functions

- **OrderProcessorFunction** : Traitement des messages SQS avec gestion d'erreurs (batch = 10)

## 3 Commandes SAM
### 1. Test Local
```bash
sam local invoke OrderProcessorFunction -e event.json -t sam-api.yml
```

### 2. Deploy
```bash
sam deploy --template-file sam-api.yml --stack-name poshub-app-sqs --s3-bucket poshub-dev-bucket --capabilities CAPABILITY_IAM --parameter-overrides ParameterKey=Stage,ParameterValue=dev
```


### 3. Test Production (amount = -1)
```bash
aws sqs send-message \
  --queue-url https://sqs.eu-north-1.amazonaws.com/ACCOUNT_ID/poshub-orders-dev \
  --message-body '{ "orderId": "7", "totalAmount": -1, "currency": "USD" }'
```

---






---

**Branche** : `feature/dlq`  
**Auteur** : Chapitre 5 - POSHub SQS System  

# Chapter 5: Lambda SQS/DLQ

## 2. SAM Commands
```bash
sam build -t sam-min-external.yml
sam local invoke OrderProcessorFunction --container-host 127.0.0.1 -t sam-min-external.yml -e events/sqs-event-create_order.json
sam deploy --template-file sam-min-external.yml --stack-name poshub-app-sqs --s3-bucket poshub-dev-bucket --capabilities CAPABILITY_IAM --parameter-overrides Stage=dev
```

## 3. SQS Tests (PowerShell)
```powershell
# Valid order
aws sqs send-message --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h --message-body '{\"date\": \"2025-01-08 18:45:00\", \"source\": \"aws cli\", \"order\": {\"orderId\": \"test-123\", \"createdAt\": \"1751996700\", \"totalAmount\": 150, \"currency\": \"USD\"}}'

# DLQ test (negative amount)
aws sqs send-message --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h --message-body '{\"date\": \"2025-01-08 18:45:00\", \"source\": \"aws cli\", \"order\": {\"orderId\": \"test-dlq\", \"createdAt\": \"1751996700\", \"totalAmount\": -1, \"currency\": \"USD\"}}'
```