from flask import Flask, render_template, request, redirect, url_for
from flask import flash, jsonify
from sqlalchemy import create_engine
from database_setup import Base, Category, Item
from sqlalchemy.orm import sessionmaker


engine = create_engine(
    'sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


app = Flask(__name__)


# Creating API Endpoints
@app.route('/categories/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Catalog=[i.serialize for i in categories])


@app.route('/categories/<int:category_id>/JSON')
def categoryItemJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=[item.serialize])


@app.route('/')
@app.route('/categories/')
def showAllCategories():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)


@app.route('/categories/new/', methods=['GET', 'POST'])
def createCategory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('New Category Created')
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('newCategory.html')


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
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
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('Category Deleted')
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete)


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return render_template('item.html', category=category, items=items)


@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def createCategoryItem(category_id):
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        flash('New Item Created')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('newItem.html', category_id=category_id)


@app.route('/categories/<int:category_id>/items/<int:item_id>/edit/', methods=['GET', 'POST'])
def editCategoryItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    itemName = editedItem.name
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
        return render_template('editItem.html', category_id=category_id, item_id=item_id, item=editedItem)


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteCategoryItem(category_id, item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    itemName = itemToDelete.name
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('%s Successfully Deleted' % itemName)
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteItem.html', category_id=category_id, item_id=item_id, item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'DZwvMguwMraRm10Mwk'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
