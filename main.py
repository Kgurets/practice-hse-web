from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


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


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CommentCreate(BaseModel):
    post_id: int
    user_id: int
    content: str


class FavoriteCreate(BaseModel):
    user_id: int
    post_id: int


class SubscriptionCreate(BaseModel):
    subscriber_id: int
    target_user_id: int

class PostCategoryCreate(BaseModel):
    post_id: int
    category_id: int


def load_data() -> None:
    global users_db, posts_db, categories_db, comments_db, favorites_db, subscriptions_db, next_user_id, next_post_id, next_category_id, next_comment_id
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users_db = data.get("users", {})
                posts_db = data.get("posts", {})
                categories_db = data.get("categories", {})
                comments_db = data.get("comments", {})
                favorites_db = data.get("favorites", {})
                subscriptions_db = data.get("subscriptions", {})
                next_user_id = data.get("next_user_id", 1)
                next_post_id = data.get("next_post_id", 1)
                next_category_id = data.get("next_category_id", 1)
                next_comment_id = data.get("next_comment_id", 1)
        else:
            users_db = {}
            posts_db = {}
            categories_db = {}
            comments_db = {}
            favorites_db = {}
            subscriptions_db = {}
            next_user_id = 1
            next_post_id = 1
            next_category_id = 1
            next_comment_id = 1
            save_data()
    except Exception:
        users_db = {}
        posts_db = {}
        categories_db = {}
        comments_db = {}
        favorites_db = {}
        subscriptions_db = {}
        next_user_id = 1
        next_post_id = 1
        next_category_id = 1
        next_comment_id = 1
        save_data()


def save_data() -> None:
    data = {
        "users": users_db,
        "posts": posts_db,
        "categories": categories_db,
        "comments": comments_db,
        "favorites": favorites_db,
        "subscriptions": subscriptions_db,
        "next_user_id": next_user_id,
        "next_post_id": next_post_id,
        "next_category_id": next_category_id,
        "next_comment_id": next_comment_id,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


load_data()


@app.get("/")
async def read_root(request: Request) -> Any:
    posts = list(posts_db.values())
    for post in posts:
        author_id = str(post["author_id"])
        if author_id in users_db:
            post["author_name"] = users_db[author_id]["login"]
        else:
            post["author_name"] = "Unknown"
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "posts": posts,
        "users": list(users_db.values()),
        "categories": list(categories_db.values())
    })


@app.get("/posts/create")
async def create_post_page(request: Request) -> Any:
    return templates.TemplateResponse(
        "create_post.html", {
            "request": request, 
            "users": list(users_db.values()),
            "categories": list(categories_db.values())
        }
    )


@app.post("/posts/create")
async def create_post_form(
    author_id: int = Form(...), title: str = Form(...), content: str = Form(...)
) -> RedirectResponse:
    author_id_str = str(author_id)
    if author_id_str not in users_db:
        raise HTTPException(status_code=404, detail="Author not found")

    global next_post_id
    post_id = next_post_id
    next_post_id += 1

    new_post = {
        "id": post_id,
        "author_id": author_id_str,
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    posts_db[post_id] = new_post
    save_data()
    return RedirectResponse(url="/", status_code=303)


@app.get("/posts/edit/{post_id}")
async def edit_post_page(request: Request, post_id: int) -> Any:
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        "edit_post.html",
        {"request": request, "post": posts_db[post_id], "users": list(users_db.values())},
    )


@app.post("/posts/edit/{post_id}")
async def edit_post_form(
    post_id: int, title: str = Form(...), content: str = Form(...)
) -> RedirectResponse:
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    posts_db[post_id]["title"] = title
    posts_db[post_id]["content"] = content
    posts_db[post_id]["updated_at"] = datetime.now().isoformat()
    save_data()
    return RedirectResponse(url="/", status_code=303)


@app.get("/posts/{post_id}")
async def read_post_page(request: Request, post_id: int) -> Any:
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    post = posts_db[post_id]
    author_id = str(post["author_id"])
    author_name = users_db[author_id]["login"] if author_id in users_db else "Unknown"

    post_comments = []
    for comment in comments_db.values():
        if comment["post_id"] == post_id:
            comment_author_id = str(comment["user_id"])
            comment["author_name"] = users_db[comment_author_id]["login"] if comment_author_id in users_db else "Unknown"
            post_comments.append(comment)

    post["categories"] = post.get("categories", [])

    return templates.TemplateResponse(
        "post.html", {
            "request": request, 
            "post": post, 
            "author_name": author_name,
            "comments": post_comments,
            "users": list(users_db.values())
        }
    )

@app.post("/api/users/")
async def create_user(user: UserCreate) -> Dict[str, Any]:
    global next_user_id
    user_id = next_user_id
    next_user_id += 1

    new_user = {
        "id": user_id,
        "email": user.email,
        "login": user.login,
        "password": user.password,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    users_db[str(user_id)] = new_user
    save_data()
    return new_user


@app.get("/api/users/")
async def get_all_users() -> List[Dict[str, Any]]:
    return list(users_db.values())


@app.get("/api/users/{user_id}")
async def get_user(user_id: int) -> Dict[str, Any]:
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id_str]


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user: UserCreate) -> Dict[str, Any]:
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    users_db[user_id_str].update(
        {
            "email": user.email,
            "login": user.login,
            "password": user.password,
            "updated_at": datetime.now().isoformat(),
        }
    )

    save_data()
    return users_db[user_id_str]


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int) -> Dict[str, str]:
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    del users_db[user_id_str]
    save_data()
    return {"message": "User deleted successfully"}


@app.post("/api/posts/")
async def create_post(post: PostCreate) -> Dict[str, Any]:
    global next_post_id
    author_id_str = str(post.author_id)
    if author_id_str not in users_db:
        raise HTTPException(status_code=404, detail="Author not found")

    post_id = next_post_id
    next_post_id += 1

    new_post = {
        "id": post_id,
        "author_id": author_id_str,
        "title": post.title,
        "content": post.content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    posts_db[post_id] = new_post
    save_data()
    return new_post


@app.get("/api/posts/")
async def get_all_posts() -> List[Dict[str, Any]]:
    return list(posts_db.values())


@app.get("/api/posts/{post_id}")
async def get_post(post_id: int) -> Dict[str, Any]:
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]


@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate) -> Dict[str, Any]:
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
async def delete_post(post_id: int) -> Dict[str, str]:
    post_id_str = str(post_id)
    if post_id_str not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    del posts_db[post_id_str]
    save_data()
    return {"message": "Post deleted successfully"}


@app.post("/api/categories/")
async def create_category(category: CategoryCreate) -> Dict[str, Any]:
    global next_category_id
    category_id = next_category_id
    next_category_id += 1

    new_category = {
        "id": category_id,
        "name": category.name,
        "description": category.description,
        "created_at": datetime.now().isoformat(),
    }

    categories_db[category_id] = new_category
    save_data()
    return new_category


@app.get("/api/categories/")
async def get_all_categories() -> List[Dict[str, Any]]:
    return list(categories_db.values())


@app.get("/api/categories/{category_id}")
async def get_category(category_id: int) -> Dict[str, Any]:
    if category_id not in categories_db:
        raise HTTPException(status_code=404, detail="Category not found")
    return categories_db[category_id]


@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: int) -> Dict[str, str]:
    if category_id not in categories_db:
        raise HTTPException(status_code=404, detail="Category not found")

    del categories_db[category_id]
    save_data()
    return {"message": "Category deleted successfully"}


@app.post("/api/comments/")
async def create_comment(comment: CommentCreate) -> Dict[str, Any]:
    global next_comment_id
    comment_id = next_comment_id
    next_comment_id += 1

    post_id_str = str(comment.post_id)
    user_id_str = str(comment.user_id)

    if post_id_str not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    new_comment = {
        "id": comment_id,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    comments_db[comment_id] = new_comment
    save_data()
    return new_comment


@app.get("/api/comments/")
async def get_all_comments() -> List[Dict[str, Any]]:
    return list(comments_db.values())


@app.get("/api/comments/{comment_id}")
async def get_comment(comment_id: int) -> Dict[str, Any]:
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comments_db[comment_id]


@app.get("/api/posts/{post_id}/comments")
async def get_post_comments(post_id: int) -> List[Dict[str, Any]]:
    post_comments = []
    for comment in comments_db.values():
        if comment["post_id"] == post_id:
            post_comments.append(comment)
    return post_comments


@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: int) -> Dict[str, str]:
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")

    del comments_db[comment_id]
    save_data()
    return {"message": "Comment deleted successfully"}


@app.post("/api/favorites/")
async def create_favorite(favorite: FavoriteCreate) -> Dict[str, Any]:
    user_id_str = str(favorite.user_id)
    post_id_str = str(favorite.post_id)

    if user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if int(favorite.post_id) not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    favorite_key = f"{favorite.user_id}_{favorite.post_id}"

    new_favorite = {
        "user_id": favorite.user_id,
        "post_id": favorite.post_id,
        "created_at": datetime.now().isoformat(),
    }

    favorites_db[favorite_key] = new_favorite
    save_data()
    return new_favorite


@app.get("/api/favorites/")
async def get_all_favorites() -> List[Dict[str, Any]]:
    return list(favorites_db.values())


@app.get("/api/users/{user_id}/favorites")
async def get_user_favorites(user_id: int) -> List[Dict[str, Any]]:
    user_favorites = []
    for favorite in favorites_db.values():
        if favorite["user_id"] == user_id:
            user_favorites.append(favorite)
    return user_favorites


@app.delete("/api/favorites/{user_id}/{post_id}")
async def delete_favorite(user_id: int, post_id: int) -> Dict[str, str]:
    favorite_key = f"{user_id}_{post_id}"
    if favorite_key not in favorites_db:
        raise HTTPException(status_code=404, detail="Favorite not found")

    del favorites_db[favorite_key]
    save_data()
    return {"message": "Favorite deleted successfully"}


@app.post("/api/subscriptions/")
async def create_subscription(subscription: SubscriptionCreate) -> Dict[str, Any]:
    subscriber_id_str = str(subscription.subscriber_id)
    target_user_id_str = str(subscription.target_user_id)

    if subscriber_id_str not in users_db:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    if target_user_id_str not in users_db:
        raise HTTPException(status_code=404, detail="Target user not found")
    if subscription.subscriber_id == subscription.target_user_id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to yourself")

    subscription_key = f"{subscription.subscriber_id}_{subscription.target_user_id}"

    new_subscription = {
        "subscriber_id": subscription.subscriber_id,
        "target_user_id": subscription.target_user_id,
        "created_at": datetime.now().isoformat(),
    }

    subscriptions_db[subscription_key] = new_subscription
    save_data()
    return new_subscription


@app.get("/api/subscriptions/")
async def get_all_subscriptions() -> List[Dict[str, Any]]:
    return list(subscriptions_db.values())


@app.get("/api/users/{user_id}/subscriptions")
async def get_user_subscriptions(user_id: int) -> List[Dict[str, Any]]:
    user_subscriptions = []
    for subscription in subscriptions_db.values():
        if subscription["subscriber_id"] == user_id:
            user_subscriptions.append(subscription)
    return user_subscriptions


@app.get("/api/users/{user_id}/subscribers")
async def get_user_subscribers(user_id: int) -> List[Dict[str, Any]]:
    user_subscribers = []
    for subscription in subscriptions_db.values():
        if subscription["target_user_id"] == user_id:
            user_subscribers.append(subscription)
    return user_subscribers


@app.delete("/api/subscriptions/{subscriber_id}/{target_user_id}")
async def delete_subscription(subscriber_id: int, target_user_id: int) -> Dict[str, str]:
    subscription_key = f"{subscriber_id}_{target_user_id}"
    if subscription_key not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")

    del subscriptions_db[subscription_key]
    save_data()
    return {"message": "Subscription deleted successfully"}


@app.get("/api/")
async def root() -> Dict[str, str]:
    return {"message": "Web Project API is working!"}

@app.post("/api/post_categories/")
async def create_post_category(post_category: PostCategoryCreate) -> Dict[str, Any]:
    post_id_str = str(post_category.post_id)
    if int(post_category.post_id) not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if post_category.category_id not in categories_db:
        raise HTTPException(status_code=404, detail="Category not found")

    # Для простоты храним категории в посте
    if "categories" not in posts_db[int(post_category.post_id)]:
        posts_db[int(post_category.post_id)]["categories"] = []
    
    category = categories_db[post_category.category_id]
    if category not in posts_db[int(post_category.post_id)]["categories"]:
        posts_db[int(post_category.post_id)]["categories"].append(category)
    
    save_data()
    return {"message": "Category added to post"}


@app.get("/api/posts/{post_id}/categories")
async def get_post_categories(post_id: int) -> List[Dict[str, Any]]:
    post_id = int(post_id)
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return posts_db[post_id].get("categories", [])

@app.post("/api/post_categories/")
async def create_post_category(post_category: PostCategoryCreate) -> Dict[str, Any]:
    post_id_str = str(post_category.post_id)
    if int(post_category.post_id) not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if post_category.category_id not in categories_db:
        raise HTTPException(status_code=404, detail="Category not found")

    if "categories" not in posts_db[int(post_category.post_id)]:
        posts_db[int(post_category.post_id)]["categories"] = []
    
    category = categories_db[post_category.category_id]
    if category not in posts_db[int(post_category.post_id)]["categories"]:
        posts_db[int(post_category.post_id)]["categories"].append(category)
    
    save_data()
    return {"message": "Category added to post"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)