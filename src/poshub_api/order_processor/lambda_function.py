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
                order = message_body.get('order', {})
                order_id = order.get('orderId')
                total_amount = order.get('totalAmount')
                message_id = record['messageId']
                source = message_body.get('source', 'unknown')
                
                logger.info(f"Processing message {message_id}: {message_body}")
                logger.info(f"Processing message from {source} at {message_body.get('date')}")
                
                # Check for error condition (negative amount)
                if total_amount == -1:
                    error_msg = f"Fail to process order {order_id} from message #{message_id} beacause must be totalAmount != -1"
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