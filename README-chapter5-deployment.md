# Chapter 5: POSHub SQS/DLQ Deployment Guide

## Overview
Ce README documente le déploiement et les tests du système SQS/DLQ pour le Chapitre 5 du projet POSHub.

## Architecture Déployée
- **Queue SQS principale** : `poshub-orders-dev-h`
- **Dead Letter Queue** : `poshub-orders-dlq-dev-h`
- **Lambda NewOrderFunction** : `poshub-new-order-lambda-dev`
- **Lambda OrderProcessor** : `poshub-order-processor-dev`

## Étapes de Déploiement

### 1. Suppression de la Stack Précédente
```bash
aws cloudformation delete-stack --stack-name poshub-app-sqs
```

### 2. Attendre la Suppression Complète
```bash
aws cloudformation wait stack-delete-complete --stack-name poshub-app-sqs
```

### 3. Déploiement du Nouveau Template
```bash
cd rest-api
sam deploy --template-file sam-min-external.yml --stack-name poshub-app-sqs --s3-bucket poshub-dev-bucket --capabilities CAPABILITY_IAM --parameter-overrides Stage=dev
```

## Résultats du Déploiement

### Ressources Créées
```
Key                 OrderProcessorArn
Description         ARN de la fonction OrderProcessor
Value               arn:aws:lambda:eu-north-1:471448382724:function:poshub-order-processor-dev

Key                 NewOrderLambdaArn
Description         ARN de la fonction NewOrderLambda
Value               arn:aws:lambda:eu-north-1:471448382724:function:poshub-new-order-lambda-dev

Key                 OrderQueueUrl
Description         URL de la queue SQS principale (existante)
Value               https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h

Key                 OrderDLQUrl
Description         URL de la Dead Letter Queue (existante)
Value               https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dlq-dev-h
```

## Tests

### 1. Test d'Envoi de Message SQS (PowerShell)
```powershell
aws sqs send-message --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h --message-body '{\"date\": \"2025-01-08 18:45:00\", \"source\": \"aws cli\", \"order\": {\"orderId\": \"test-123\", \"createdAt\": \"1751996700\", \"totalAmount\": 150, \"currency\": \"USD\"}}'
```

**Résultat Attendu :**
```json
{
    "MD5OfMessageBody": "c968029e5e6d9c2f1b1a29dc920801b6",
    "MessageId": "b11136f2-cfd9-43a9-895f-2170af41578f"
}
```

### 2. Vérification des Log Groups
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/poshub-order-processor"
```

**Résultat :**
```json
{
    "logGroups": [
        {
            "logGroupName": "/aws/lambda/poshub-order-processor-dev",
            "creationTime": 1751997256171,
            "metricFilterCount": 0,
            "arn": "arn:aws:logs:eu-north-1:471448382724:log-group:/aws/lambda/poshub-order-processor-dev:*",
            "storedBytes": 0,
            "logGroupClass": "STANDARD",
            "logGroupArn": "arn:aws:logs:eu-north-1:471448382724:log-group:/aws/lambda/poshub-order-processor-dev"
        }
    ]
}
```

### 3. Test Local des Fonctions Lambda

#### Test OrderProcessor (Ordre Valide)
```bash
sam local invoke OrderProcessorFunction --container-host 127.0.0.1 -t sam-min-external.yml -e events/sqs-event-create_order.json
```

#### Test OrderProcessor (Montant Négatif - DLQ)
```bash
sam local invoke OrderProcessorFunction --container-host 127.0.0.1 -t sam-min-external.yml -e events/sqs-event-negative-amount.json
```

### 4. Test de la Dead Letter Queue

Pour tester le mécanisme DLQ, envoyez un message avec `totalAmount: -1` :

```powershell
aws sqs send-message --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h --message-body '{\"date\": \"2025-01-08 18:45:00\", \"source\": \"aws cli\", \"order\": {\"orderId\": \"test-dlq\", \"createdAt\": \"1751996700\", \"totalAmount\": -1, \"currency\": \"USD\"}}'
```

Ce message échouera 3 fois (maxReceiveCount) puis sera automatiquement transféré vers la DLQ.

## Monitoring

### Consulter les Logs de Traitement
```bash
aws logs tail /aws/lambda/poshub-order-processor-dev --follow
```

### Vérifier les Messages dans les Queues
```bash
# Queue principale
aws sqs get-queue-attributes --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dev-h --attribute-names ApproximateNumberOfMessages

# Dead Letter Queue
aws sqs get-queue-attributes --queue-url https://sqs.eu-north-1.amazonaws.com/471448382724/poshub-orders-dlq-dev-h --attribute-names ApproximateNumberOfMessages
```

## Fichiers de Configuration

### Template SAM
- **Fichier** : `rest-api/sam-min-external.yml`
- **Stack** : `poshub-app-sqs`
- **Région** : `eu-north-1`

### Événements de Test
- **Ordre valide** : `rest-api/events/sqs-event-create_order.json`
- **Ordre invalide** : `rest-api/events/sqs-event-negative-amount.json`

## Notes Importantes

1. **Queues Existantes** : Le template utilise les queues SQS existantes (suffixe `-h`)
2. **Retry Mechanism** : 3 tentatives avant envoi vers DLQ
3. **Batch Processing** : BatchSize de 10 messages par invocation
4. **Error Handling** : ReportBatchItemFailures activé pour la gestion granulaire des échecs

---

**Statut** : ✅ Déploiement réussi  
**Date** : 2025-01-08  
**Branche** : `feature/rest-api` 