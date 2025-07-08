import json
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Process order messages from SQS and log them.
    """
    try:
        batch_item_failures = []
        
        logger.info(f"Received event with {len(event['Records'])} records")
        
        for record in event['Records']:
            try:
                # Extract message body
                message_body = json.loads(record['body'])
                order_id = message_body.get('orderId')
                message_id = record['messageId']
                
                logger.info(f"Processing message {message_id}: {message_body}")
                
                # Log order processing
                logger.info("order traité", extra={"order_id": order_id, "message_id": message_id})
                
                # Check for error condition
                if message_body.get("amount") == -1:
                    error_msg = f"Fail to process order {order_id} from message #{message_id} because amount cannot be -1"
                    logger.error(f"Error in process_message: {error_msg}")
                    raise ValueError("Fail to process order")
                
                logger.info(f"Successfully processed message {message_id}")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error processing message {record['messageId']}: {str(e)}")
                # Add failed message to batch failures
                batch_item_failures.append({
                    "itemIdentifier": record['messageId']
                })
        
        # Return batch item failures for SQS to handle retries
        return {
            "batchItemFailures": batch_item_failures
        }
        
    except Exception as e:
        logger.error("Unexpected error in lambda_handler", exc_info=e)
        # If there's an unexpected error, fail all messages
        return {
            "batchItemFailures": [{"itemIdentifier": record['messageId']} for record in event.get('Records', [])]
        } 