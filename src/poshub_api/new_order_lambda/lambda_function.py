import json
import logging
import os

import boto3
from fastapi import FastAPI
from mangum import Mangum

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS SQS client
sqs_client = boto3.client('sqs')

# FastAPI app
app = FastAPI()

@app.post("/create-order")
async def create_order(order: dict):
    """
    Create an order and send a message to SQS.
    """
    try:
        # Log order creation
        logger.info("Creating order", extra={"order_id": order.get("orderId")})

        # Send message to SQS
        response = sqs_client.send_message(
            QueueUrl=os.getenv("SQS_QUEUE_URL"),  # Ensure this environment variable is set
            MessageBody=json.dumps(order)
        )

        # Log message ID
        message_id = response['MessageId']
        logger.info("Message sent to SQS", extra={"message_id": message_id})

        return {"status": "success", "message_id": message_id}
    except Exception as e:
        logger.error("Error creating order", exc_info=e)
        return {"status": "error", "message": str(e)}

# AWS Lambda handler
lambda_handler = Mangum(app) 