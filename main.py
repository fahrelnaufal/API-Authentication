from os import write
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "b59bb529c691acfd3e89a0cf8256adb3581d7dbc07e43871645fda73eb28e335"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


db_user = {
    "asdf": {
        "username": "asdf",
        "hashed_password": "$2b$12$M/V0vRjczr9lGCAFsW7pfeE84GHR/AAmhQ6tZnXfPa5wkaMTO3c1m",
        "disabled": False,
    },
    "Fahrel": {
        "username": "Fahrel",
        "hashed_password": "$2b$12$Y6/RIh01zAvvR8Nur7Jobuj5lI531lJ6O39w4Gt/DxknjTSDNm34C",
        "disabled": False,
    },
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

with open("menu.json","r") as read_file:
	data = json.load(read_file)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

# Function Verifikasi Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function Get Hash Password
def get_password_hash(password):
    return pwd_context.hash(password)

# Function Get User
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

# Function Autentikasi User
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Function Buat Akses Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_token(token: str = Depends(oauth2_scheme)):
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db_user, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
			status_code=400,
			detail="Inactive user"
		)
    return current_user

# Post Token
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db_user, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get User
@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Get All
@app.get("/")
def root(current_user: User = Depends(get_current_active_user)):
	return{'Menu','Item'}

# Read Menus
@app.get("/menu")
async def read_menus(current_user: User = Depends(get_current_active_user)):
	return data

# Read Menu
@app.get("/menu/{item_id}")
async def read_menu(item_id : int, current_user: User = Depends(get_current_active_user)):
	for menu_item in data['menu']:
		if menu_item['id'] == item_id:
			return menu_item
	raise HTTPException( # Membuat Excpetion Handling
			status_code = 404,
			detail = f'Item not found!'
		)

# Add Menu
@app.post('/menu')
async def add_menu(name : str, current_user: User = Depends(get_current_active_user)):
	id = 1
	if(len(data['menu']) > 0):
		id = data['menu'][len(data['menu']) - 1]['id']+1
	n_data = {'id': id,'name' : name}
	data['menu'].append(dict(n_data))
	read_file.close()
	with open("menu.json","w") as write_file:
		json.dump(data,write_file,indent = 4)
	write.file.close()
		
	return n_data

# Update Menu
@app.put("/menu/{item_id}")
async def update_menu(item_id : int, name : str, current_user: User = Depends(get_current_active_user)):
	for menu_item in data['menu']:
		if menu_item['id'] == item_id:
			menu_item['name'] = name
			read_file.close()
			with open("menu.json","w") as write_file:
				json.dump(data,write_file,indent = 4)
			write.file.close()

			return("message : Data updated!") # return pesan data terupdate

	raise HTTPException( # Membuat Excpetion Handling
			status_code = 404,
			detail = f'Item not found!'
		)

# Delete Menu
@app.delete("/menu/{item_id}")
async def delete_menu(item_id : int, current_user: User = Depends(get_current_active_user)):
	for menu_item in data['menu']:
		if menu_item['id'] == item_id:
			data['menu'].remove(menu_item)
			read_file.close()
			with open("menu.json","w") as write_file:
				json.dump(data,write_file,indent = 4) 
			write.file.close()

			return("message : Data deleted!") # return pesan data terhapus

	raise HTTPException( # Membuat Excpetion Handling
			status_code = 404,
			detail = f'Item not found!'
		)