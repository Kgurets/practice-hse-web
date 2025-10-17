erDiagram
    users {
        SERIAL id PK
        VARCHAR email
        VARCHAR login
        VARCHAR password_hash
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    categories {
        SERIAL id PK
        VARCHAR name
        TEXT description
        TIMESTAMP created_at
    }
    
    posts {
        SERIAL id PK
        INTEGER author_id FK
        VARCHAR title
        TEXT content
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    comments {
        SERIAL id PK
        INTEGER post_id FK
        INTEGER user_id FK
        TEXT content
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    favorites {
        INTEGER user_id PK,FK
        INTEGER post_id PK,FK
        TIMESTAMP created_at
    }
    
    subscriptions {
        INTEGER subscriber_id PK,FK
        INTEGER target_user_id PK,FK
        TIMESTAMP created_at
    }
    
    post_categories {
        INTEGER post_id PK,FK
        INTEGER category_id PK,FK
    }
    
    users ||--o{ posts : writes
    users ||--o{ comments : writes
    users ||--o{ favorites : has
    users ||--o{ subscriptions : subscribes_to
    users ||--o{ subscriptions : subscribed_by
    posts ||--o{ comments : has
    posts }o--o{ categories : tagged_with
    posts }o--o{ users : favorited_by