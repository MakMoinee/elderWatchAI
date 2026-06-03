import requests

def send_sms(api_key="3234|E1BKl3SDvX5mn54jnGlbDbNWwzLwEINw8D1qwFlQ47354438 ", recipient_number="639766045802", message=None, sender_name="PhilSMS"):
    url = "https://dashboard.philsms.com/api/v3/sms/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "recipient": recipient_number,
        "sender_id": sender_name,
        "message": message
    }
    try:
        print(f"Sending SMS to {recipient_number}...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"SMS API Response: {result}")
                print("SMS sent successfully!")
                return result
            except Exception as json_err:
                print(f"SMS sent but failed to parse response: {json_err}")
                return {"raw": response.text}
        else:
            print(f"SMS failed with status code: {response.status_code} — {response.text}")
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        print(f"ERROR sending SMS: {e}")
        return {"error": str(e)}

send_sms(message="This is a message from ElderWatchAI. Verifiying that the SMS API integration is working correctly.")
