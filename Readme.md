# Blog Application

This is a Flask application for creating and managing blog posts. The app allows users to register, log in, create,
edit, and delete blog posts. Users can also comment on and rate posts. There is an admin-only section for managing user
permissions.

## Features

- User registration and login
- Create, edit, and delete blog posts
- Comment on posts
- Rate posts
- Create, edit, and delete comments and ratings 
- Admin-only section for managing user permissions
- CKEditor for rich text input
- Bootstrap 5 integration for styling

## Technology Used

- **Programming Language:** Python
- **Framework:** Flask
- **Database:** SQLAlchemy local PostgreSQL deployed
- **Styling:** Bootstrap 5
- **Rich Text Editor:** CKEditor
- **Gravatar Integration:** Gravatar
- **User Authentication:** Flask-Login
- **Task Queue:** Celery (for potential future enhancements)
- **Message Broker:** Redis (for potential future enhancements)

## Requirements

- Python 3.7+
- Flask
- Flask-Bootstrap
- Flask-CKEditor
- Flask-Login
- Flask-SQLAlchemy
- Flask-WTF
- Flask-Gravatar
- Flask-Migrate
- Python-dotenv

## Installation

1. Clone the repository:

    ```bash
    git https://github.com/osstd/The_Blog_.git
    cd The_blog
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables. Create a `.env` file in the project root directory and add the following:

    ```env
    SECRET_KEY=your_secret_key
    DB_URI=your_database_uri
    F_KEY=your_flask_secret_key
    MY_EMAIL=your_email
    MY_EMAIL_PASSWORD=your_email_password
    A_ID=your_twilio_account_sid
    A_T=your_twilio_auth_token
    S_ID=your_twilio_phone_number
    T_ID=your_phone_number
    ```

   Replace the placeholders with your actual values.

5. Initialize the database:

    ```bash
    flask db upgrade
    ```

6. Run the application:

    ```bash
    flask run
    ```

## Usage

### Routes

- `/` : Home page displaying all blog posts
- `/register` : User registration page
- `/login` : User login page
- `/logout` : User logout
- `/post/<int:post_id>` : View a specific post with comments and ratings
- `/new-post` : Create a new post (requires login)
- `/edit-post/<int:post_id>` : Edit an existing post (requires login)
- `/delete/<int:post_id>` : Delete a post (requires login)
- `/request-posting` : Request permission to add posts (requires login)
- `/process-posting/<int:user_id>/<int:user_allow>` : Admin route to process posting requests
- `/permission` : Admin route to view and manage user posting requests
- `/deletecom/<int:comment_id>` : Delete a comment (requires login)
- `/deleterat/<int:rating_id>` : Delete a rating (requires login)
- `/edit-comment/<int:comment_id>` : Edit a comment (requires login)
- `/edit-rating/<int:rating_id>` : Edit a rating (requires login)
- `/user` : User profile page (requires login)
- `/about` : About page
- `/contact` : Contact form page (requires login)

### Admin-Only Features

The application includes a decorator `@admin_only` that restricts access to certain routes to admin users (typically
user with ID 1).

### Forms

- `RegisterForm` : For user registration
- `LoginForm` : For user login
- `CreatePostForm` : For creating and editing blog posts
- `CommentForm` : For adding and editing comments
- `RatingForm` : For adding and editing ratings

## Database Models

- `UserBlog` : Represents a user in the application with fields for ID, email, password, name, and related posts,
  comments, and ratings.
- `BlogPost` : Represents a blog post with fields for ID, author ID, title, subtitle, date, body, image URL, and related
  comments and ratings.
- `Comment` : Represents a comment with fields for ID, post ID, author ID, and text.
- `Rating` : Represents a rating with fields for ID, post ID, author ID, and value.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
