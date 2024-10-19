from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import os

# --------SETUP FLASK & MONGODB--------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # get key from env

client = MongoClient(os.getenv("MONGO_URI"))   # get URI connection from env
JobTracker = client[os.getenv("MONGO_DBNAME")] # get database name from env

users_collection = JobTracker["users"]                # collection of users
applications_collection = JobTracker["applications"]  # collection of applications


# --------ACCOUNT PAGE--------
@app.route("/account")
def account():
    return render_template("account.html") # link to html


# --------LOGIN PAGE--------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get data
        email = request.form.get("email")
        password = request.form.get("password")

        # authenticate user
        user = users_collection.find_one({"email": email})

        if user and user["password"] == password:
            session["user_id"] = str(user["_id"])   # set session user_id
            session["username"] = user["username"]  # set session username
            return redirect(url_for("index"))       # direct to home page
        else: return redirect(url_for("login"))

    return render_template("login.html") # link to html


# --------SIGNUP PAGE--------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # get data
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # check if user exists
        existing_user = users_collection.find_one({"email":email})
        if existing_user: return redirect(url_for("signup"))
        
        # insert new user into users collection
        new_user = {
            "email": email,
            "username": username,
            "password": password
        }
        users_collection.insert_one(new_user)
        return redirect(url_for("login")) # direct to login page

    return render_template("signup.html") # link to html


# --------HOME PAGE--------
@app.route("/")
def index():
    if "user_id" not in session: return redirect(url_for("login")) 
    
    # get all applications from current user
    user_id = session.get("user_id")
    applications = applications_collection.find({"user_id": user_id})
    
    return render_template("index.html", applications=applications, username=session.get("username"))


# --------ADD PAGE--------
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        # get data
        date = request.form.get("date")
        company = request.form.get("company")
        industry = request.form.get("industry")
        position = request.form.get("position")
        status = request.form.get("status")

        # insert new application into applications collection
        new_application = {
            "user_id": session.get("user_id"),
            "date": date,
            "company": company,
            "industry": industry,
            "position": position,
            "status": "applied"    # always "applied" when first added
        }
        applications_collection.insert_one(new_application)
        return redirect(url_for("index")) # direct to home page
    
    return render_template("add.html") # link to html


# --------EDIT PAGE--------
@app.route("/edit/<application_id>", methods=["GET", "POST"])
def edit(application_id):
    if "user_id" not in session: return redirect(url_for("login")) # direct to login page

    # ensure it's current user's applications
    application = applications_collection.find_one(
        {"_id": ObjectId(application_id),
        "user_id": session.get("user_id")}
    )
    if not application: return redirect(url_for("index")) # direct to home page

    if request.method == "POST":
        # get data
        date = request.form.get("date")
        company = request.form.get("company")
        industry = request.form.get("industry")
        position = request.form.get("position")
        status = request.form.get("status")

        # update application
        applications_collection.update_one(
            {"_id": ObjectId(application_id), "user_id": session.get("user_id")},
            {"$set": {
                "date": date,
                "company": company,
                "industry": industry,
                "position": position,
                "status": status
            }}
        )
        return redirect(url_for("index")) # direct to home page

    return render_template("edit.html", application=application) # link to html


# --------DELETE PAGE--------
@app.route("/delete/<application_id>", methods=["GET", "POST"])
def delete(application_id):
    if "user_id" not in session: return redirect(url_for("login")) # direct to login page

    # ensure it's current user's application
    application = applications_collection.find_one({
        "_id": ObjectId(application_id),
        "user_id": session.get("user_id")}
    )
    if not application: return redirect(url_for("index")) # direct to home page

    # delete application
    if request.method == "POST":
        applications_collection.delete_one({"_id": ObjectId(application_id), "user_id": session.get("user_id")})
        return redirect(url_for("index")) # direct to home page

    return render_template("delete.html", application=application) # link to html


# --------SEARCH PAGE--------
@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session: return redirect(url_for("login")) # direct to login page

    # query variables
    query = {"user_id": session.get("user_id")} # user-specific
    category = request.form.get("category")
    search_value = request.form.get(category)

    print(f"Searching by {category} with value {search_value}")  # Debugging print

    # query based on chosen category
    if category:
        # text fields (company, industry, position) --> partial matching
        if category in ["company", "industry", "position"]:
            if isinstance(search_value, str): query[category] = {"$regex": search_value, "$options": "i"} 
        
        # exact matches (date, status) --> direct matching
        elif category == "date": query["date"] = search_value
        elif category == "status": query["status"] = search_value 

    applications = list(applications_collection.find(query)) # search by category

    return render_template("search.html", applications=applications, category=category) # link to html


# --------SORT PAGE--------
@app.route("/sort", methods=["GET", "POST"])
def sort():
    if "user_id" not in session: return redirect(url_for("login")) # direct to login page

    if request.method == "POST":
        # get data
        category = request.form.get("category")
        order = request.form.get("order")
        
        # set sort order: 1 = ascending, -1 = descending
        if order == "asc": sort_order = 1
        else: sort_order = -1

        # query to find applications
        query = {"user_id": session.get("user_id")}

        # sort applications
        applications = list(applications_collection.find(query).sort(category, sort_order))
        return render_template("sort.html", applications=applications)

    return render_template("sort.html", applications=[]) # link to html


# --------LOGOUT PAGE--------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("account")) # link to html


# --------RUN--------
if __name__ == "__main__":
    app.run(debug=True)