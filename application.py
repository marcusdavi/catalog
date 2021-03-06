from models import Category, User, Item, Base
from flask import Flask, render_template, jsonify, request
from flask import url_for, abort, g, redirect, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, asc, desc
from flask import make_response
import requests
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "YOUR_APPLICATION_NAME_HERE"

engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),  # noqa
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))  # noqa
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON for Show All Categories.
@app.route('/categoryJSON', methods=['GET', 'POST'])
def showAllCategoriesJSON():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return jsonify(categories=[category.serialize
                       for category in categories])


# JSON for Show All Items of a Category.
@app.route('/category/<string:category_name>/JSON',
           methods=['GET', 'POST'])
def showCategoryItemsJSON(category_name):
    if request.method == 'GET':
        category = session.query(Category).filter_by(name=category_name).one()
        items = session.query(Item).filter_by(cat_id=category.id).all()  # noqa
        return jsonify(items=[item.serialize for item in items])  # noqa


# JSON for Show a Item.
@app.route('/category/<string:category_name>/<string:item_name>/JSON',
           methods=['GET', 'POST'])
def showItemJSON(category_name, item_name):
    if request.method == 'GET':
        category = session.query(Category).filter_by(name=category_name).one()
        item = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
        return jsonify(item.serialize)  # noqa


# Function for Show All Categories.
@app.route('/', methods=['GET', 'POST'])
@app.route('/category', methods=['GET', 'POST'])
def showAllCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    lastestItems = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template('categories.html',
                            categories=categories, items=lastestItems)  # noqa


# Function for Show a Category Items.
@app.route('/category/<string:category_name>', methods=['GET', 'POST'])
def showCategoryItems(category_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(cat_id=category.id).all()
    return render_template('categoryitems.html',
                           category_name=category_name, items=items)


# Function for Show a Item Selected.
@app.route('/category/<string:category_name>/<string:item_name>/showItem',
           methods=['GET', 'POST'])
def ShowItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    itemToShow = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    return render_template('showitem.html',
                           category_name=category_name, item=itemToShow)


# Function for Create a Item.
@app.route('/category/<string:category_name>/newitem', methods=['GET', 'POST'])
def NewCategoryItem(category_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       cat_id=category.id, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCategoryItems',
                        category_name=category_name))
    else:
        return render_template('newcategoryitem.html',
                               category_name=category_name)


# Function for Edit a Item. Only the creator can Edit.
@app.route('/category/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def EditCategoryItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    editedMenuItem = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    if login_session['user_id'] != editedMenuItem.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit this item.');}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['name']:
            editedMenuItem.name = request.form['name']
        if request.form['description']:
            editedMenuItem.description = request.form['description']
        session.add(editedMenuItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showCategoryItems',
                        category_name=category_name))
    else:
        return render_template('editcategoryitem.html',
                               category_name=category_name,
                               item_name=item_name, item=editedMenuItem)


# Function for Delete a Item. Only the creator can Delete.
@app.route('/category/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
def DeleteCategoryItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    itemToDelete = session.query(Item).filter_by(cat_id=category.id).filter_by(name=item_name).one()  # noqa
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete this item.');}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCategoryItems',
                                category_name=category_name))
    else:
        return render_template('deletecategoryitem.html',
                               category_name=category_name,
                               item_name=item_name,
                               item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showAllCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showAllCategories'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
