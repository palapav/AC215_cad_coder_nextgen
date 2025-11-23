from fastapi import APIRouter, Request, HTTPException
from app.services.auth_service import verify_google_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/google")
async def google_login(request: Request):
    """
    Verifies Google ID token sent from React frontend and returns user info.
    """
    data = await request.json()
    token = data.get("credential")

    if not token:
        raise HTTPException(status_code=400, detail="Missing Google credential token")

    user_info = verify_google_token(token)
    if "error" in user_info:
        raise HTTPException(status_code=401, detail=user_info["error"])

    return {"user": user_info, "auth_method": "google", "status": "success"}
