from models import Category, User, Item, Base
from flask import Flask, jsonify, request, url_for, abort, g
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
# from flask.ext.httpauth import HTTPBasicAuth

# auth = HTTPBasicAuth()

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

# ADD @auth.verify_password here

# ADD a /users route here


@app.route('/categoryJSON', methods = ['GET','POST'])
#protect this route with a required login
def showAllCategoriesJSON():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return jsonify(categories = [category.serialize for category in categories])

@app.route('/category', methods = ['GET','POST'])
#protect this route with a required login
def showAllCategories():
	return "This Page will show all my categories"
		
@app.route('/category/<string:category_name>', methods = ['GET','POST'])
#protect this route with a required login
def showCategoryItems(category_name):
	return "This Page is the items for category %s" % category_name
		
@app.route('/category/<string:category_name>/newitem', methods = ['GET','POST'])
#protect this route with a required login
def NewCategoryItem(category_name):
	return "This page is for making a new Item for category %s" % category_name
		
@app.route('/category/<string:category_name>/<string:item_name>/edit', methods = ['GET','POST'])
#protect this route with a required login
def EditCategoryItem(category_name, item_name):
	return "This Page will be editing Category Item  %S" % item_name
		
@app.route('/category/<string:category_name>/<string:item_name>/delete', methods = ['GET','POST'])
#protect this route with a required login
def DeleteCategoryItem(category_name, item_name):
	return "This Page will be deleting a Category Item  %s" % item_name

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
