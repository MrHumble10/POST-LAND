from __future__ import print_function
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import date
import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from forms import PostForm, RegisterForm, LoginForm, CommentForm
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user
from functools import wraps
from flask_gravatar import Gravatar
import os
from notifications import send_email

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy()
db.init_app(app)

ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.String, nullable=False)
    tel = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship("BlogPost", back_populates="author")
    comments = db.relationship("Comment", back_populates="author_comment")


# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = db.relationship("Comment", back_populates="post_comment")


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(30), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author_comment = db.relationship("User", back_populates="comments")
    # relationship with BlogPost
    post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"))
    post_comment = db.relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()



# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash('You need to log out to access the register page')
        return redirect(url_for('get_all_posts'))

    form = RegisterForm()
    psw_hashed_with_salt = generate_password_hash(f'{form.password.data}',
                                                  method='pbkdf2:sha256',
                                                  salt_length=8
                                                  )
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            age=form.age.data,
            tel=form.tel.data,
            email=form.email.data,
            password=psw_hashed_with_salt,
        )
        # if username is in DB so direct users in login page
        result = db.session.execute(db.Select(User).where(User.email == new_user.email))
        user = result.scalar()
        if user:
            flash(f"* {user.email} *  has already signed up. Log In instead!")
            return redirect(url_for('login'))
        else:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.Select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash("This Email doesn't exist, try again please")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("The password is wrong, try again please")
            return redirect(url_for('login'))
        else:
            login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/')
def get_all_posts():
    # TODO: Query the database for all the posts. Convert the data to a python list.
    result = db.session.execute(db.Select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated)


underline = '\u0332\u0332'


# TODO: Add a route so that you can click on individual posts.

@app.route('/<int:post_id>', methods=["GET", "POST"])
def show_post(post_id):
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    today = dt.datetime.now().strftime("%Y-%m-%d")
    if form.validate_on_submit():

        if not current_user.is_authenticated:
            flash(f"Log in is required to comment for {'   '}{underline.join(requested_post.title)}{underline}")
            return redirect(url_for('login'))
        new_comment = Comment(
            comment=form.comment.data,
            date=today,
            author_comment=current_user,
            post_comment=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(f"{requested_post.id}")
    return render_template("post.html", post=requested_post,
                           form=form,
                           logged_in=current_user.is_authenticated,
                           number_of_days=days_ago, today=today)


# TODO: add_new_post() to create a new blog post
@app.route("/new_post", methods=["GET", "POST"])
@admin_only
def new_post():
    form = PostForm()
    post_date = dt.datetime.now().strftime("%Y-%m-%d")
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=current_user,
            img_url=form.img_url.data,
            body=form.body.data,
            date=post_date
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    if not current_user.is_authenticated:
        flash("Log in is required to create a new post ")
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


# TODO: edit_post() to change an existing blog post
@app.route("/edit_post<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        author=post.author,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.author = current_user
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=edit_form, is_edit_post=True, logged_in=current_user)


# TODO: delete_post() to remove a blog post from the database
@app.route("/delete<int:post_id>")
@admin_only
def delete(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    logged_in = current_user.is_authenticated
    if not logged_in:
        flash("To contact us please log in.")
        return redirect(url_for("get_all_posts"))
    else:
        if request.method == "POST":
            print(request.form["name"])
            send_email(request.form["name"], request.form["email"], request.form["phone"], request.form["message"])
            return render_template("contact.html", logged_in=current_user.is_authenticated, msg_sent=True)

    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# <-----------------------------COMMENT SECTOR--------------------------------------->

gravatar = Gravatar(
    app=app,
    size=80,
    rating='g',
    default='robohash',
    force_default=False,
    use_ssl=False,
    base_url=None

)


def days_ago(from_str, to_str):
    date_from = dt.datetime.strptime(from_str, "%Y-%m-%d")
    date_to = dt.datetime.strptime(to_str, "%Y-%m-%d")
    days = (date_from - date_to).days

    # to get rid of " - " for example -25 days ago. It
    # has been simplified to * -1 to reach a positive number.
    return days * -1


# @app.route("/editcmt<int:comment_id>")
# def edit_comment(comment_id):
#     cmt = db.get_or_404(Comment, comment_id)
#     post = db.get_or_404(BlogPost, cmt.post_id)
#     edit_form = PostForm(
#         body=post.body
#     )
#     if edit_form.validate_on_submit():
#         cmt.comment = edit_form.body.data
#         db.session.commit()
#         return redirect(f"{cmt.post_id}")
#     return render_template("post.html", edit_comment=True)


@app.route("/delcmt<int:comment_id>")
def del_comment(comment_id):
    comment_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(f"{comment_to_delete.post_id}")

# ------------------------------MORSE CODE----------------------------------------->

CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.',
    'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..',
    'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-',
    'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '1': '.----',
    '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '0': '-----',
    ' ': '/', '13': '\n'
}

CODE_REVERSED = {value: key for (key, value) in CODE.items()}


def to_morse(s):
    return ' '.join(CODE.get(i.upper()) for i in s)


def from_morse(s):
    return ''.join(CODE_REVERSED.get(i) for i in s.split())

@app.route('/morse', methods=['GET', "POST"])
def morse():
    if request.method == 'POST':
        if request.form['p'] == 'from_morse':
            p = from_morse(request.form['message'])
        else:
            p = to_morse(request.form['message'])
        return render_template("morse.html", f=p, logged_in=current_user.is_authenticated)
    return render_template("morse.html", logged_in=current_user.is_authenticated)

if __name__ == "__main__":
    app.run(debug=True, port=5003)
