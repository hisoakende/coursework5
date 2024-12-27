import json
from datetime import datetime

import pika
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import ALGORITHM, SECRET_KEY, RABBITMQ_URL
import database
import schemas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените * на список разрешенных доменов в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user_id


def send_message_to_rabbitmq(message):
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue='email_notifications')
    channel.basic_publish(exchange='', routing_key='email_notifications', body=json.dumps(message))
    connection.close()


@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = database.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/token", response_model=schemas.AccessToken)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"user_id": user.id})
    return schemas.AccessToken(access_token=access_token, token_type="bearer")


@app.post("/subscriptions", response_model=schemas.Subscription)
async def create_subscription(subscription: schemas.SubscriptionCreate, user_id: int = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    db_subscription = database.Subscription(user_id=user_id, journal_id=subscription.journal_id)
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


@app.get("/subscriptions", response_model=list[schemas.Subscription])
async def get_subscriptions(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscriptions = db.query(database.Subscription).filter(database.Subscription.user_id == current_user).all()
    return subscriptions


@app.post("/posts", response_model=schemas.Post)
async def create_post(post: schemas.PostCreate, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    journal = db.query(database.Journal).filter(database.Journal.id == post.journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found.")
    if journal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not the owner of this journal.")
    db_post = database.Post(**post.dict(), user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    message = {
        "journal_id": post.journal_id,
        "journal_name": journal.name,
        "post_content": db_post.text,
        "datetime": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "emails": [
            user.email
            for user in db.query(database.User).filter(
                database.User.id.in_(db.query(database.Subscription.user_id).filter(
                    database.Subscription.journal_id == post.journal_id)
                )
            )
        ]
    }
    if message["emails"]:
        send_message_to_rabbitmq(message)

    return db_post


@app.post("/journals", response_model=schemas.Journal)
async def create_journal(journal: schemas.JournalCreate, user_id: int = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    db_journal = database.Journal(**journal.dict(), user_id=user_id)
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    return db_journal


@app.get("/journals", response_model=list[schemas.Journal])
async def get_all_journals(db: Session = Depends(get_db)):
    return db.query(database.Journal).all()


@app.get("/journals/search", response_model=list[schemas.Journal])
async def search_journals(query: str = Query(""), db: Session = Depends(get_db)):
    return db.query(database.Journal).filter(database.Journal.name.contains(query)).all()


@app.get("/journals/user", response_model=list[schemas.Journal])
async def get_user_journals(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(database.Journal).filter(database.Journal.user_id == user_id).all()


@app.delete("/journals/{journal_id}", response_model=schemas.Journal)
async def delete_journal(journal_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    db_journal = db.query(database.Journal).filter(database.Journal.id == journal_id).first()
    if not db_journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    if db_journal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not the owner of this journal.")
    db.delete(db_journal)
    db.commit()
    return db_journal


@app.delete("/subscriptions/{journal_id}", status_code=204)
async def delete_subscription(journal_id: int, current_user: int = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    subscription = db.query(database.Subscription).filter(
        database.Subscription.journal_id == journal_id,
        database.Subscription.user_id == current_user
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscripion not found")

    db.delete(subscription)
    db.commit()

    return {"detail": "Subscription deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyfQ.OEeC6DAMkUhVNEF-XGbmYZdlux4JPK1wLuO9z0lKQbs
