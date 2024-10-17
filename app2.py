from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# # setup Flask and MongoDB
# load_dotenv()
# app = Flask(__name__)
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") # load key from .env

# client = MongoClient(os.getenv("MONGO_URI"))  # use MongoClient directly
# db = client[os.getenv("MONGO_DBNAME")]        # database name
# collection = db["applications"]               # collection name

# # add.html
# @app.route("/add", methods=["GET", "POST"])
# def add():
#     if request.method == "POST":

#         # setup variables
#         date = request.form["date"]
#         company = request.form["company"]
#         industry = request.form["industry"]
#         position = request.form["position"]
#         status = request.form["status"]

#         # insert data into variables
#         new_application = {
#             "date": date,
#             "company": company,
#             "industry": industry,
#             "position": position,
#             "status": status
#         }
#         collection.insert_one(new_application) # store in database
#         return redirect(url_for("home"))       # redirect to home()
    
#     return render_template("add.html") # GET request -> render add.html

# @app.route("/")
# def home():
#     return render_template("index.html")

# # run code
# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
