import datetime
import os

# Get current date
current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Format the message
message = f"Framework test successful on {current_date}"

# Create the file with the message
with open('framework_test_success.txt', 'w') as file:
    file.write(message)

print(f"File created with content: {message}")

# List directory contents to confirm file existence
print("\nDirectory contents:")
files = os.listdir('.')
for file in files:
    print(f"- {file}")

# Verify the file exists
if 'framework_test_success.txt' in files:
    print("\n✓ framework_test_success.txt successfully created and verified!")
else:
    print("\n✗ File creation failed!")