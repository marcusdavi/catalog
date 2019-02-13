from models import Category, User, Item, Base
from flask import Flask, render_template, jsonify, request
from flask import url_for, abort, g, redirect, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, asc, desc
from flask import make_response
import requests
import httplib2
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json

# from flask.ext.httpauth import HTTPBasicAuth

# auth = HTTPBasicAuth()

engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

# ADD @auth.verify_password here

# ADD a /users route here


@app.route('/categoryJSON', methods=['GET', 'POST'])
# protect this route with a required login
def showAllCategoriesJSON():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return jsonify(categories=[category.serialize for category in categories])  # noqa


@app.route('/', methods=['GET', 'POST'])
@app.route('/category', methods=['GET', 'POST'])
# protect this route with a required login
def showAllCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    lastestItems = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template('categories.html',
                            categories=categories, items=lastestItems)  # noqa


@app.route('/category/<string:category_name>', methods=['GET', 'POST'])
def showCategoryItems(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(cat_id=category.id).all()
    return render_template('categoryitems.html',
                           category_name=category_name, items=items)


@app.route('/category/<string:category_name>/<string:item_name>/showItem',
           methods=['GET', 'POST'])
# protect this route with a required login
def ShowItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    itemToShow = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    return render_template('showitem.html',
                           category_name=category_name, item=itemToShow)


@app.route('/category/<string:category_name>/newitem', methods=['GET', 'POST'])
# protect this route with a required login
def NewCategoryItem(category_name):
    if request.method == 'POST':
        category = session.query(Category).filter_by(name=category_name).one()
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       cat_id=category.id, user_id='1')
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCategoryItems',
                        category_name=category_name))
    else:
        return render_template('newcategoryitem.html',
                               category_name=category_name)


@app.route('/category/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
# protect this route with a required login
def EditCategoryItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    editedMenuItem = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedMenuItem.name = request.form['name']
        if request.form['description']:
            editedMenuItem.description = request.form['description']
        session.add(editedMenuItem)
        session.commit()
        return redirect(url_for('showCategoryItems',
                        category_name=category_name))
    else:
        return render_template('editcategoryitem.html',
                               category_name=category_name,
                               item_name=item_name, item=editedMenuItem)


@app.route('/category/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
# protect this route with a required login
def DeleteCategoryItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    itemToDelete = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategoryItems',
                                category_name=category_name))
    else:
        return render_template('deletecategoryitem.html',
                               category_name=category_name,
                               item_name=item_name,
                               item=itemToDelete)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
