import time
import random

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from starlette import status

from app.security import create_access_token, hash_password
from app.database import  User
import bcrypt
from app.schemas import UserLogin, Register, VerifyOTP, ForgotPasswordRequest, ResetPasswordRequest, ResendOTPRequest
from app.deps import get_db
from app.services.Email_service import send_registration_otp_email, send_password_reset_email


router = APIRouter()


unverified_users = {}
password_reset_requests = {}




@router.post("/register")
def register(user: Register, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email, User.is_verified == True).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A verified account with this email already exists.")

    hashed_pw = hash_password(user.password)
    otp = str(random.randint(100000, 999999))
    expiry_time = time.time() + (10 * 60)

    unverified_users[user.email] = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": hashed_pw,
        "otp": otp,
        "expiry": expiry_time
    }

    email_response = send_registration_otp_email(user.email, otp)
    if not email_response["success"]:
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")

    return {"message": "Registration initiated. Please check your email for a verification OTP."}


@router.post("/verify-otp")
def verify_otp(request: VerifyOTP, db: Session = Depends(get_db)):
    temp_user_data = unverified_users.get(request.email)

    if not temp_user_data or time.time() > temp_user_data["expiry"]:
        raise HTTPException(status_code=400, detail="OTP is invalid or has expired. Please register again.")

    if temp_user_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")

    new_user = User(
        username=temp_user_data["username"],
        first_name=temp_user_data["first_name"],
        last_name=temp_user_data["last_name"],
        email=request.email,
        password=temp_user_data["password"],
        is_verified=True  # Set the user as verified
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    del unverified_users[request.email]

    return {"message": "Account verified successfully!", "user_id": new_user.id}



@router.post("/resend-otp")
def resend_otp(request: ResendOTPRequest):
    """
    Resends an OTP for either user registration or password reset based on the provided context.
    """
    new_otp = str(random.randint(100000, 999999))
    new_expiry_time = time.time() + (10 * 60)  # Set a new 10-minute expiry

    if request.context == "register":
        # Check if there's a pending registration for this email
        if request.email not in unverified_users:
            raise HTTPException(status_code=404,
                                detail="No pending registration found for this email. Please register again.")

        # Update the user's OTP and expiry time
        unverified_users[request.email]["otp"] = new_otp
        unverified_users[request.email]["expiry"] = new_expiry_time

        # Resend the registration email
        email_response = send_registration_otp_email(request.email, new_otp)
        if not email_response["success"]:
            raise HTTPException(status_code=500, detail="Failed to send OTP email.")

        return {"message": "A new verification OTP has been sent to your email."}

    elif request.context == "forgot_password":
        # Check if there's a pending password reset request
        if request.email not in password_reset_requests:
            raise HTTPException(status_code=404,
                                detail="No active password reset request found. Please initiate one again.")

        # Update the OTP and expiry time
        password_reset_requests[request.email]["otp"] = new_otp
        password_reset_requests[request.email]["expiry"] = new_expiry_time

        # Resend the password reset email
        email_response = send_password_reset_email(request.email, new_otp)
        if not email_response["success"]:
            raise HTTPException(status_code=500, detail="Failed to send OTP email.")

        return {"message": "A new password reset OTP has been sent to your email."}

    else:
        raise HTTPException(status_code=400, detail="Invalid context provided. Use 'register' or 'forgot_password'.")





@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/token", summary="Login for Swagger UI/OAuth2")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == form_data.username).first()

    if not db_user or not bcrypt.checkpw(form_data.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email, User.is_verified == True).first()
    if not user:
        # Return a generic message to prevent user enumeration attacks
        return {"message": "If an account with this email exists, a password reset OTP has been sent."}

    otp = str(random.randint(100000, 999999))
    expiry_time = time.time() + (10 * 60)  # OTP valid for 10 minutes

    password_reset_requests[request.email] = {
        "otp": otp,
        "expiry": expiry_time
    }

    email_response = send_password_reset_email(request.email, otp)
    if not email_response["success"]:
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")

    return {"message": "If an account with this email exists, a password reset OTP has been sent."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_data = password_reset_requests.get(request.email)

    if not reset_data or time.time() > reset_data["expiry"]:
        raise HTTPException(status_code=400, detail="OTP is invalid or has expired. Please try again.")

    if reset_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")

    # Find the user to update their password
    user_to_update = db.query(User).filter(User.email == request.email).first()
    if not user_to_update:
        # Should not happen if forgot-password was called correctly, but good to have a check
        raise HTTPException(status_code=404, detail="User not found.")

    user_to_update.password = hash_password(request.new_password)
    db.commit()

    del password_reset_requests[request.email]

    return {"message": "Password has been reset successfully."}
