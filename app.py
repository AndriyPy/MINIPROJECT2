from fastapi import Depends, FastAPI, HTTPException, status
import uvicorn
from db import create_tables, get_db, hash_password, check_password
import aiosqlite
from pydantic import BaseModel, EmailStr, SecretStr, Field
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


app = FastAPI(on_startup=(create_tables,))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="token value", examples=["#3HM4J24V324kljn2"])

class User(BaseModel):
    username: str = Field(
        description="User name", min_length=3, examples=["Bob", "Jack", "Benjamin"]
    )
    email: EmailStr = Field(description="User email", examples=["john@exampl.com"])
    password: SecretStr = Field(
        description="User's password. Minimum 6 characters.",
        min_length=6
    )

class Post(BaseModel):
    title: str = Field(description="Title of the post",examples=["Selling a bike"])
    description: str = Field(description="Content or description of the post",examples=["Mountain bike in great condition"])



@app.post("/token",
    response_model=Token,
    summary="User login",
    description="Authenticates a user using email and password.",
    response_description="Access token and token type")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: aiosqlite.Connection = Depends(get_db),
):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
        user = await cursor.fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not check_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "access_token": user["email"],
        "token_type": "bearer"
    }


async def get_user(
    token: str = Depends(oauth2_scheme),
    connection: aiosqlite.Connection = Depends(get_db)
):
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?", (token,)
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user



@app.post("/create_user",
          summary="Register a new user",
          description="Creates a new user with a hashed password.",
          response_description="Confirmation message"
          )
async def create_user(user: User, connection: aiosqlite.Connection = Depends(get_db)):
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?", (user.email,)
        )
        db_user = await cursor.fetchone()
        if db_user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User with this email exist")

        hashed_pwd = hash_password(user.password.get_secret_value())

        await cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (user.username, user.email, hashed_pwd)
        )

        await connection.commit()
    return {"message": "User created successfully"}




@app.post("/create_post",
          summary="Create a new post",
          description="Creates a new post associated with the currently authenticated user.",
          response_description="Confirmation message"
          )
async def create_post(
        post:Post,
        connection: aiosqlite.Connection = Depends(get_db),
        current_user: dict = Depends(get_user),):
    async with connection.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO posts (user_id, title, description) VALUES (?, ?, ?)
            """,
            (current_user["id"], post.title, post.description)
        )
        await connection.commit()
    return {"message": "Post created successfully"}



if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)