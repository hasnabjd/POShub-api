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

## Manual Steps for SQS and DLQ Configuration

### Creating SQS Queues
1. **Create Main Queue**: Go to the AWS SQS console and create a new queue named `poshub-orders-dev`.
2. **Create DLQ**: In the same console, create another queue named `poshub-orders-dlq`.

### Configuring DLQ
1. **Set DLQ for Main Queue**:
   - Navigate to the `poshub-orders-dev` queue settings.
   - Edit the `Redrive policy` to use `poshub-orders-dlq`.
   - Set `maxReceiveCount` to 3.

### Adding Lambda Trigger
1. **Add Trigger to Lambda**:
   - Go to the AWS Lambda console.
   - Select the `order_processor` Lambda function.
   - Add a trigger for the `poshub-orders-dev` SQS queue.

### Verification
1. **Test DLQ**:
   - Send a test message with `amount = -1` to `poshub-orders-dev`.
   - Verify the message appears in `poshub-orders-dlq` after three failed attempts.

These steps ensure that the SQS and DLQ are properly configured for the Lambda functions to process orders and handle errors effectively.