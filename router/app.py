from fastapi import FastAPI, HTTPException, Request
import db

app = FastAPI()

@app.post('/register')
async def user_register(request: Request):
    try:
        data = await request.json()
        data = dict(data)
        check_keys = {"username", "email", "password"}
        if check_keys != set(data.keys()):
            raise HTTPException(500, detail="wrong data keys")
        user = db.tools.Users().register(username=data["username"], password=data["password"], email=data["email"])   
        if isinstance(user, db.structure.User):
            token = db.tools.Users().get_token(user=user)
            return {"token": token.string}
        raise HTTPException(500, detail=f"server-side error: {user}")
    except Exception as e:
        raise HTTPException(500, detail=f"server-side error: {e}")
    
@app.post('/login')
async def user_login(request: Request):
    try:
        data = await request.json()
        data = dict(data)
        data_keys = list(data.keys())
        if "password" not in data_keys:
            raise HTTPException(500, detail="wrong data keys")
        user = db.tools.Users().get(username=data.get("username", None), email=data.get("email", None))
        check = user.is_password(data["password"])
        token = db.tools.Users().get_token(user=user)
        if check:
            return {"token": token.string}
        else:
            raise HTTPException(403, detail="wrong password bro")
        
    except Exception as e:
        raise HTTPException(500, detail=f"server-side error: {e}")