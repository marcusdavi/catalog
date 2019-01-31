from database_setup import Category, User, Item, Base
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


@app.route('/categories', methods=['GET', 'POST'])
# protect this route with a required login
def showAllCategories():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return jsonify(categories=[
                                  category.serialize
                                  for category in categories])

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
