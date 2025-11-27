from google.oauth2 import id_token
from google.auth.transport import requests
import logging

def verify_google_token(token: str):
    """
    Verify Google ID token sent from frontend and return user info.
    """
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "sub": idinfo.get("sub"),
        }
    except ValueError as e:
        logging.error(f"Invalid Google ID token: {e}")
        return {"error": "Invalid Google ID token"}
    except Exception as e:
        logging.error(f"Auth verification failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    fake_token = "your_test_token_here"
    print(verify_google_token(fake_token))