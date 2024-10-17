from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)          #####  MODIFY


uri = 'mongodb+srv://bh2422:dOCLFnnJBAK1SFyS@rbfdatabase.fyphm.mongodb.net/' 


# MongoDB connection
client = MongoClient(uri)
db = client['job_tracker']
users_collection = db['users']
applications_collection = db['applications']

# Flask-Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    @staticmethod
    def get_user_by_username(username):
        user_data = users_collection.find_one({'username': username})
        if user_data:
            return user_data
        return None

    @staticmethod
    def get_user_by_id(user_id):
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return user_data
        return None

@login_manager.user_loader
def load_user(user_id):
    user_data = User.get_user_by_id(user_id)
    if user_data:
        return User(user_id=str(user_data['_id']))
    return None

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('register'))

        # Hash the password and insert user into MongoDB
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            'username': username,
            'password': hashed_password
        })
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = User.get_user_by_username(username)
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_id=str(user_data['_id']))
            login_user(user)
            return redirect(url_for('retrieve'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Retrieve all applications (protected route)
@app.route('/retrieve')
@login_required
def retrieve():
    applications = list(applications_collection.find({'user_id': current_user.id}))  # Get only the logged-in user's applications
    return render_template('retrieve.html', applications=applications)

# Add new job application (protected route)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        job_title = request.form['job_title']
        company = request.form['company']
        status = request.form['status']
        date_applied = request.form['date_applied']
        
        # Insert new application into MongoDB, tied to the current user
        applications_collection.insert_one({
            'job_title': job_title,
            'company': company,
            'status': status,
            'date_applied': date_applied,
            'user_id': current_user.id
        })
        return redirect(url_for('retrieve'))
    return render_template('add.html')

# Edit job application (protected route)
@app.route('/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    application = applications_collection.find_one({'_id': ObjectId(id), 'user_id': current_user.id})
    if not application:
        return "Application not found or unauthorized", 403

    if request.method == 'POST':
        job_title = request.form['job_title']
        company = request.form['company']
        status = request.form['status']
        date_applied = request.form['date_applied']
        
        # Update application in MongoDB
        applications_collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'job_title': job_title,
                'company': company,
                'status': status,
                'date_applied': date_applied
            }}
        )
        return redirect(url_for('retrieve'))
    return render_template('edit.html', application=application)

# Delete job application (protected route)
@app.route('/delete/<string:id>')
@login_required
def delete(id):
    # Delete application from MongoDB
    applications_collection.delete_one({'_id': ObjectId(id), 'user_id': current_user.id})
    return redirect(url_for('retrieve'))

# Search for applications (protected route)
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_term = request.form['search_term']
        
        # Search for applications by job title or company in MongoDB, specific to the logged-in user
        results = applications_collection.find({
            '$and': [
                {'user_id': current_user.id},
                {'$or': [
                    {'job_title': {'$regex': search_term, '$options': 'i'}},
                    {'company': {'$regex': search_term, '$options': 'i'}}
                ]}
            ]
        })
        return render_template('search.html', results=list(results))
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)