import requests
import json

# Replace with the actual URL of your API Gateway endpoint
api_url = "https://your-api-gateway-url.amazonaws.com/dev/create-order"

# Define the test order payload
test_order = {
    "orderId": "test-order-123",
    "amount": -1  # This will trigger the error condition
}

# Send the POST request
response = requests.post(api_url, json=test_order)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json()) 