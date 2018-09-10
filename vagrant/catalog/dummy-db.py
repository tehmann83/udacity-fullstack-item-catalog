from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

myFirstCategory = Category(name="NBA Champions")
session.add(myFirstCategory)
session.commit()

chicago = Item(name="Chicago Bulls 1996", description="MJ, Pip, The Worm, and The Croation Sensation. What a team!", category=myFirstCategory)
session.add(chicago)
session.commit()

gsw = Item(name="Golden State Warriors 2018", description="Steph Curry, KD, Greene, and Klay. They are already a dynasty!", category=myFirstCategory)
session.add(gsw)
session.commit()

pl = Category(name="Premierleague Champions")
session.add(pl)
session.commit()

liverpool = Item(name="Liverpool 2019", description="Will Jurgen Klopp be able to show his team the way to the holy grail this season?", category=pl)
session.add(liverpool)
session.commit()

print "Added some data."
