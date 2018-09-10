from flask import Flask, render_template
from sqlalchemy import create_engine
from database_setup import Base, Category, Item
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


app = Flask(__name__)

@app.route('/')
@app.route('/categories/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return render_template('item.html', category=category, items=items)


@app.route('/categories/<int:category_id>/new/')
def newItem(category_id):
    return "new item here"


@app.route('/categories/<int:category_id>/<int:item_id>/edit/')
def editItem(category_id, item_id):
    return "edit item here"


@app.route('/categories/<int:category_id>/<int:item_id>/delete/')
def deleteItem(category_id, item_id):
    return "delete item here"



if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
