from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt, random, time

from app.database import User
from app.deps import get_db
from app.schemas import Register, UserLogin, VerifyOTP, ResetPasswordRequest
from app.security import create_access_token, hash_password, verify_token
from app.services.Email_service import (
    send_login_otp_email,
    send_password_reset_email,
)

router = APIRouter()


login_otps = {}
password_reset_requests = {}
OTP_TTL_SECONDS = 10 * 60

@router.post("/register", summary="Register new user (superuser only)")
def register(
    user: Register,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can register new users.",
        )

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    hashed_pw = hash_password(user.password)

    new_user = User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_pw,
        is_verified=True,
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}



@router.post("/login", summary="Login with email/password (sends OTP to email)")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # generate OTP
    otp = str(random.randint(100000, 999999))
    expiry_time = time.time() + OTP_TTL_SECONDS
    login_otps[db_user.email] = {"otp": otp, "expiry": expiry_time}
    print(otp)
    # send OTP email
    email_response = send_login_otp_email(db_user.email, otp)
    if not email_response.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send login OTP email")

    return {"message": "OTP sent to registered email. Use /verify-login-otp to complete login."}


@router.post("/verify-login-otp", summary="Verify login OTP and get JWT token")
def verify_login_otp(request: VerifyOTP, db: Session = Depends(get_db)):
    otp_entry = login_otps.get(request.email)
    if not otp_entry or time.time() > otp_entry["expiry"]:
        raise HTTPException(status_code=400, detail="OTP is invalid or expired. Please login again to receive a new OTP.")

    if otp_entry["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")

    # OTP valid -> issue token
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User account not verified.")

    token = create_access_token(data={"sub": user.username,"role": user.role})
    del login_otps[request.email]

    return {"access_token": token, "token_type": "bearer"}


@router.post("/request-password-reset", summary="Request password reset OTP")
def request_password_reset(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    otp = str(random.randint(100000, 999999))
    expiry_time = time.time() + OTP_TTL_SECONDS
    password_reset_requests[email] = {"otp": otp, "expiry": expiry_time}

    email_response = send_password_reset_email(email, otp)
    if not email_response.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send password reset OTP email")

    return {"message": "Password reset OTP sent to email."}

@router.post("/verify-password-reset-otp", summary="Verify password reset OTP")
def verify_password_reset_otp(request: VerifyOTP):
    otp_entry = password_reset_requests.get(request.email)
    if not otp_entry or time.time() > otp_entry["expiry"]:
        raise HTTPException(status_code=400, detail="OTP is invalid or expired.")

    if otp_entry["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")

    return {"message": "OTP verified successfully."}

@router.post("/reset-password", summary="Reset password after OTP verification")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    otp_entry = password_reset_requests.get(request.email)
    if not otp_entry or time.time() > otp_entry["expiry"] or otp_entry["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    hashed_pw = hash_password(request.new_password)
    user.password = hashed_pw
    db.commit()

    del password_reset_requests[request.email]

    return {"message": "Password has been reset successfully."}



@router.post("/token", summary="Login for Swagger UI/OAuth2")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == form_data.username).first()

    if not db_user or not bcrypt.checkpw(form_data.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}
