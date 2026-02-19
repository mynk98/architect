#!/usr/bin/env python3

# Read and print content from stability_test.txt
try:
    with open('stability_test.txt', 'r') as file:
        content = file.read().strip()
        print(f"File content: {content}")
        if content == "OK":
            print("SUCCESS: File content matches expected value 'OK'")
        else:
            print(f"FAILURE: File content '{content}' does not match expected value 'OK'")
except FileNotFoundError:
    print("ERROR: stability_test.txt file not found")
except Exception as e:
    print(f"ERROR: {e}")
