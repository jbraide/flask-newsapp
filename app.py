from flask import Flask, render_template, url_for, redirect, request, session
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, TextAreaField, PasswordField, Form, validators
from passlib.hash import sha256_crypt
from datetime import datetime
import os

#instantiate flask app
app = Flask(__name__)

# db file location config
#project_dir = os.path.dirname(os.path.abspath(__file__))
#database_file = "sqlite:///{}".format(os.path.join(project_dir,"blog.db"))

# image upload configuration
photos = UploadSet('photos',IMAGES)

#secret key
app.secret_key = ''

# sqlalchemy inititiation
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'

configure_uploads(app,photos)


#Blog Post class
class BlogPostForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    author = StringField('Author',[validators.Length(min=1, max=200)])
    content = TextAreaField('Content',[validators.Length(min=30)])
# admin form class
class AdminForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=40)])
    password = PasswordField('Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm', message = 'Passwords do not match ')
    ])
    confirm = PasswordField('Confirm password')


#db models

#blog post database model

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img_name = db.Column(db.String(300))
    title = db.Column(db.String(100))
    author = db.Column(db.String(30))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)


# admin database model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))




# index route
@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('index.html',posts=posts)

# blog post add page route
@app.route('/add', methods=['GET','POST'])
def add():
    form = BlogPostForm(request.form)

    if request.method == 'POST' and 'image' in request.files and form.validate():
        title = form.title.data
        author = form.author.data
        content = form.content.data

        image = request.files['image']

        image_name = image.filename # request the file name of the image.

        image_store = photos.save(image) # save image to the destination folder as specified on line  26

        post = BlogPost(img_name=image_name, title=title,author=author, content=content, date_posted=datetime.now())
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('add.html',form=form)

@app.route('/post/<string:id>/')
def post(id):
    post = BlogPost.query.filter_by(id=id).first()

    return render_template('post.html',post=post)

@app.route('/edit/<string:id>/', methods=['GET','POST'])
def edit(id):
    post = BlogPost.query.filter_by(id=id).one()
    form = BlogPostForm(request.form)

    form.title.data = post.title
    form.author.data = post.author
    form.content.data = post.content

    if request.method == 'POST' and form.validate():
        title  = request.form['title']
        author = request.form['author']
        content = request.form['content']

        post.title = title
        post.author = author
        post.content = content

        db.session.commit()

        return redirect(url_for('index'))
    return render_template('edit.html',form=form)

@app.route('/delete/<string:id>', methods=['GET','POST'])
def delete(id):
    post = BlogPost.query.filter_by(id=id).one()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


#login functionality
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        result = Admin.query.filter_by(username=username).first()

        password = result.password

        if sha256_crypt.verify(password_candidate, password):
            session['logged_in'] = True
            session['username'] = username

            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Login'
            return render_template('login.html', error=error)
    return render_template('login.html')

#register functionality
@app.route('/register', methods=['GET','POST'])
def register():
    form = AdminForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        admin = Admin(username=username, password=password)
        db.session.add(admin)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# dashboard functionality
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
