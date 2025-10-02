from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import json
import os

app = FastAPI(title="Web Project")
templates = Jinja2Templates(directory="templates")

DATA_FILE = "data.json"

class UserCreate(BaseModel):
    email: str
    login: str
    password: str

class PostCreate(BaseModel):
    author_id: int
    title: str
    content: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

def load_data():
    global users_db, posts_db, next_user_id, next_post_id
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                users_db = data.get('users', {})
                posts_db = data.get('posts', {})
                next_user_id = data.get('next_user_id', 1)
                next_post_id = data.get('next_post_id', 1)
        else:
            users_db = {}
            posts_db = {}
            next_user_id = 1
            next_post_id = 1
            save_data()
    except:
        users_db = {}
        posts_db = {}
        next_user_id = 1
        next_post_id = 1
        save_data()

def save_data():
    data = {
        'users': users_db,
        'posts': posts_db,
        'next_user_id': next_user_id,
        'next_post_id': next_post_id
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

load_data()

@app.get("/")
async def read_root(request: Request):
    posts = list(posts_db.values())
    for post in posts:
        author_id = post['author_id']
        if author_id in users_db:
            post['author_name'] = users_db[author_id]['login']
        else:
            post['author_name'] = 'Unknown'
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})

@app.get("/posts/create")
async def create_post_page(request: Request):
    return templates.TemplateResponse("create_post.html", {
        "request": request, 
        "users": list(users_db.values())
    })

@app.post("/posts/create")
async def create_post_form(
    author_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...)
):
    try:
        author_id = int(author_id)
        if author_id not in users_db:
            raise HTTPException(status_code=404, detail="Author not found")
        
        post_data = PostCreate(author_id=author_id, title=title, content=content)
        result = await create_post(post_data)
        return RedirectResponse(url="/", status_code=303)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid author ID")

@app.get("/posts/edit/{post_id}")
async def edit_post_page(request: Request, post_id: int):
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return templates.TemplateResponse("edit_post.html", {
        "request": request, 
        "post": posts_db[post_id],
        "users": list(users_db.values())
    })

@app.post("/posts/edit/{post_id}")
async def edit_post_form(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...)
):
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    posts_db[post_id]["title"] = title
    posts_db[post_id]["content"] = content
    posts_db[post_id]["updated_at"] = datetime.now().isoformat()
    save_data()
    return RedirectResponse(url="/", status_code=303)

@app.get("/posts/{post_id}")
async def read_post_page(request: Request, post_id: int):
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = posts_db[post_id]
    author_id = post['author_id']
    author_name = users_db[author_id]['login'] if author_id in users_db else 'Unknown'
    
    return templates.TemplateResponse("post.html", {
        "request": request, 
        "post": post,
        "author_name": author_name
    })

@app.post("/api/users/")
async def create_user(user: UserCreate):
    global next_user_id
    user_id = next_user_id
    next_user_id += 1
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "login": user.login,
        "password": user.password,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    users_db[user_id] = new_user
    save_data()
    return new_user

@app.get("/api/users/")
async def get_all_users():
    return list(users_db.values())

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    user_id = str(user_id)
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user: UserCreate):
    user_id = str(user_id)
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    users_db[user_id].update({
        "email": user.email,
        "login": user.login,
        "password": user.password,
        "updated_at": datetime.now().isoformat()
    })
    
    save_data()
    return users_db[user_id]

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    user_id = str(user_id)
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del users_db[user_id]
    save_data()
    return {"message": "User deleted successfully"}

@app.post("/api/posts/")
async def create_post(post: PostCreate):
    global next_post_id
    post.author_id = str(post.author_id)
    if post.author_id not in users_db:
        raise HTTPException(status_code=404, detail="Author not found")
    
    post_id = next_post_id
    next_post_id += 1
    
    new_post = {
        "id": post_id,
        "author_id": post.author_id,
        "title": post.title,
        "content": post.content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    posts_db[post_id] = new_post
    save_data()
    return new_post

@app.get("/api/posts/")
async def get_all_posts():
    return list(posts_db.values())

@app.get("/api/posts/{post_id}")
async def get_post(post_id: int):
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]

@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate):
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.title:
        posts_db[post_id]["title"] = post.title
    if post.content:
        posts_db[post_id]["content"] = post.content
    
    posts_db[post_id]["updated_at"] = datetime.now().isoformat()
    save_data()
    return posts_db[post_id]

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int):
    post_id = str(post_id)
    if str(post_id) not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    del posts_db[post_id]
    save_data()
    return {"message": "Post deleted successfully"}

@app.get("/api/")
async def root():
    return {"message": "Web Project API is working!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)