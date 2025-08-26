import http.client
import json
import os

print("--- Running Direct OpenAI API Connection Test ---")

TOKEN = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    print("❌ FAILURE: OPENAI_API_KEY not found in environment!")
else:
    print(f"✅ Found OPENAI_API_KEY starting with: {TOKEN[:5]}...")
    
    try:
        print("-> Attempting to establish HTTPS connection to api.openai.com...")
        connection = http.client.HTTPSConnection("api.openai.com", timeout=15)
        
        headers = {
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # We don't need a real prompt, just a valid request to test the connection
        body = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        })
        
        print("-> Connection established. Sending request...")
        connection.request("POST", "/v1/chat/completions", body, headers)
        
        print("-> Request sent. Waiting for response...")
        response = connection.getresponse()
        
        print(f"\\n✅ SUCCESS: Connection successful!")
        print(f"-> HTTP Status: {response.status}")
        print(f"-> Response Reason: {response.reason}")
        
        response.read() # Clean up the connection
        connection.close()

    except Exception as e:
        print(f"\\n❌ FAILURE: The connection to the OpenAI API failed.")
        print("   This strongly indicates a network issue (firewall, proxy, DNS) is blocking the connection.")
        print(f"   Error details: {e}")