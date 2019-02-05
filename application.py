from models import Category, User, Item, Base
from flask import Flask, render_template, jsonify, request, url_for, abort, g, redirect, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, asc
from flask import make_response
import requests
import httplib2
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json

#from flask.ext.httpauth import HTTPBasicAuth

#auth = HTTPBasicAuth() 


engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

#ADD @auth.verify_password here

#ADD a /users route here


# Return all categories in object Json
@app.route('/categoryJSON', methods = ['GET','POST'])
#protect this route with a required login
def showAllCategoriesJSON():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return jsonify(categories = [category.serialize for category in categories])

# Page with all categories
@app.route('/', methods = ['GET','POST'])
@app.route('/category', methods = ['GET','POST'])
#protect this route with a required login
def showAllCategories():
	categories = session.query(Category).order_by(asc(Category.name))
	return render_template('categories.html', categories=categories)		

# Page with Items of the selected category
@app.route('/category/<string:category_name>', methods = ['GET','POST'])
def showCategoryItems(category_name):
	category = session.query(Category).filter_by(name=category_name).one()
	items = session.query(Item).filter_by(cat_id=category.id).all()
	return render_template('categoryitems.html', category_name=category_name, items=items)		

# Page for add a new item
@app.route('/category/<string:category_name>/newitem', methods = ['GET','POST'])
#protect this route with a required login
def NewCategoryItem(category_name):
	return "This page is for making a new Item for category %s" % category_name

# Page for edit the item selected
@app.route('/category/<string:category_name>/<string:item_name>/edit', methods = ['GET','POST'])
#protect this route with a required login
def EditCategoryItem(category_name, item_name):
	return "This Page will be editing Category Item  %S" % item_name
	
# Page for remove the item selected
@app.route('/category/<string:category_name>/<string:item_name>/delete', methods = ['GET','POST'])
#protect this route with a required login
def DeleteCategoryItem(category_name, item_name):
	return "This Page will be deleting a Category Item  %s" % item_name

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
