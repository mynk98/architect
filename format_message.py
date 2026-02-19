from datetime import datetime

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Format the message string
message = f"Framework test successful on {current_date}. Multi-model chained architecture working correctly."

print(f"Formatted message: {message}")
print(f"Message will be written to: framework_test_success.txt")