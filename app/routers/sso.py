from fastapi import Depends, APIRouter, HTTPException, Form, status,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.authentication import create_access_token, authenticate_user, SESSION_COOKIE_NAME
from database import get_db
from database_crud import users_db_crud as db_crud
from schemas import User, UserSignUp
import os 
from dotenv import load_dotenv
from fastapi_sso.sso.google import GoogleSSO
from schemas import UserSignUp
from fastapi_sso.sso.microsoft import MicrosoftSSO


router = APIRouter(prefix="/sso")


@router.post("/sign_up", response_model=User, summary="Register a user", tags=["Auth"])
def create_user(user_signup: UserSignUp, db: Session = Depends(get_db)):
    """
    Registers a user.
    """
    try:
        user_created = db_crud.add_user(db, user_signup)
        return user_created
    except db_crud.DuplicateError as e:
        raise HTTPException(status_code=403, detail=f"{e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.post("/login", summary="Login as a user", tags=["Auth"])
def login(response: RedirectResponse, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Logs in a user.
    """
    user = authenticate_user(db=db, username=username, password=password, provider='local')
    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid username or password.")
    try:
        access_token = create_access_token(username=user.username, provider='local')
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE_NAME, access_token)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.post("/logout", summary="Logout a user", tags=["Auth"])
def logout():
    """
    Logout a user.
    """
    try:
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")
    

    load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_sso = GoogleSSO(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    f"{os.getenv('HOST')}/v1/google/callback"
)

router = APIRouter(prefix="/v1/google")


@router.get("/login", tags=['Google SSO'])
async def google_login():
    async with google_sso:
        return await google_sso.get_login_redirect(params={"prompt": "consent", "access_type": "offline"})


@router.get("/callback", tags=['Google SSO'])
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Process login response from Google and return user info"""

    try:
        async with google_sso:
            user = await google_sso.verify_and_process(request)
        user_stored = db_crud.get_user(db, user.email, provider=user.provider)
        if not user_stored:
            user_to_add = UserSignUp(
                username=user.email,
                fullname=user.display_name
            )
            user_stored = db_crud.add_user(db, user_to_add, provider=user.provider)
        access_token = create_access_token(username=user_stored.username, provider=user.provider)
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE_NAME, access_token)
        return response
    except db_crud.DuplicateError as e:
        raise HTTPException(status_code=403, detail=f"{e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")
    

    load_dotenv()
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")


microsoft_sso = MicrosoftSSO(
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    f"{os.getenv('HOST')}/v1/microsoft/callback"
)

router = APIRouter(prefix="/v1/microsoft")


@router.get("/login", tags=['Microsoft SSO'])
async def microsoft_login():
    async with microsoft_sso:
        return await microsoft_sso.get_login_redirect()


@router.get("/callback", tags=['Microsoft SSO'])
async def microsoft_callback(request: Request, db: Session = Depends(get_db)):
    """Process login response from Microsoft and return user info"""

    try:
        async with microsoft_sso:
            user = await microsoft_sso.verify_and_process(request)
        user_stored = db_crud.get_user(db, user.email, user.provider)
        if not user_stored:
            user_to_add = UserSignUp(
                username=user.email if user.email else user.display_name,
                fullname=user.display_name
            )
            user_stored = db_crud.add_user(db, user_to_add, provider=user.provider)
        access_token = create_access_token(username=user_stored.username, provider=user.provider)
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE_NAME, access_token)
        return response
    except db_crud.DuplicateError as e:
        raise HTTPException(status_code=403, detail=f"{e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")