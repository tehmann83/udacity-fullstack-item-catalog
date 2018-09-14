#!/usr/bin/env python
from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   make_response)
from sqlalchemy import create_engine, asc
from database_setup import Base, Category, Item, User
from sqlalchemy.orm import sessionmaker
from functools import wraps

# Imports for oauth2
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

engine = create_engine(
    'sqlite:///usersCatalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

# Load google signin API client id
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def showLogin():
    '''Route to login page'''
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    '''Connect to google account'''
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data  # .decode('utf-8')

    try:
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
    # Submit request, parse response
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    # login_session['access_token'] = access_token
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    # params = {'access_token': access_token, 'alt': 'json'}
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = \
    "width: 300px; \
        height: 300px; \
        border-radius: 150px; \
        -webkit-border-radius: 150px; \
        -moz-border-radius: 150px;" > '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    '''Creates a user
       Args: login_session
       Returns: id of user'''
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    '''Returns user object
       Args: user_id'''
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    '''Returns user ID
       Args: email from user login_session'''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    '''Disconnects user'''
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token
    print 'user name: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result: '
    print result

    if result['status'] == '200':
        # Reset user session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Creating API Endpoints
@app.route('/categories/JSON')
def catalogJSON():
    '''Returns all categories with their items as JSON'''
    categories = session.query(Category).all()
    return jsonify(Catalog=[i.serialize for i in categories])


@app.route('/categories/<int:category_id>/JSON')
def categoryItemJSON(category_id):
    '''Returns a categories items as JSON
       Args: id of category'''
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    '''Returns an item as JSON
       Args: IDs of category and item'''
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=[item.serialize])


@app.route('/')
@app.route('/categories/')
def showAllCategories():
    '''Route to page where all categories are listed'''
    categories = session.query(Category).order_by(asc(Category.name))  # .all()
    if 'username' not in login_session:
        return render_template('publicCategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)


@app.route('/categories/new/', methods=['GET', 'POST'])
def createCategory():
    '''Route to page where new categories may be created'''
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New Category Created')
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('newCategory.html')


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    '''Route to page where categories may be edited
       Args: ID of category'''
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        return "\
        <script>\
        function reject() {alert('Access denied.');}\
        </script>\
        <body onload='reject()'"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        session.commit()
        flash('Category Successfully Edited')
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)


@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    '''Route to page where categories may be deleted
       Args: ID of category'''
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return "\
        <script>\
        function reject() {alert('Access denied.');}\
        </script>\
        <body onload='reject()'"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('Category Deleted')
        return redirect(url_for('showAllCategories'))
    else:
        return render_template(
            'deleteCategory.html', category=categoryToDelete)


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showCategory(category_id):
    '''Route to page where a category's items are listed
       Args: ID of category'''
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template(
            'publicItem.html', category=category, items=items, creator=creator)
    else:
        return render_template(
            'item.html', category=category, items=items, creator=creator)


@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def createCategoryItem(category_id):
    '''Route to page where items may be created
       Args: ID of category'''
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if category.user_id != login_session['user_id']:
        return "\
        <script>\
        function reject() {alert('Access denied.');}\
        </script>\
        <body onload='reject()'"
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New Item Created')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('newItem.html', category_id=category_id)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/edit/',
    methods=['GET', 'POST'])
def editCategoryItem(category_id, item_id):
    '''Route to page where categories may be edited
       Args: ID of category and item'''
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    itemName = editedItem.name
    if category.user_id != login_session['user_id']:
        return "\
        <script>\
        function reject() {alert('Access denied.');}\
        </script>\
        <body onload='reject()'"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('%s Successfully Edited' % itemName)
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template(
            'editItem.html',
            category_id=category_id,
            item_id=item_id,
            item=editedItem)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/delete/',
    methods=['GET', 'POST'])
def deleteCategoryItem(category_id, item_id):
    '''Route to page where categories may be deleted
       Args: ID of category and item'''
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    itemName = itemToDelete.name
    if category.user_id != login_session['user_id']:
        return "\
        <script>\
        function reject() {alert('Access denied.');}\
        </script>\
        <body onload='reject()'"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('%s Successfully Deleted' % itemName)
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template(
            'deleteItem.html',
            category_id=category_id,
            item_id=item_id,
            item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'DZwvMguwMraRm10Mwk'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
