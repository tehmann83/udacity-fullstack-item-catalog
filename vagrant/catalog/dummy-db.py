#!/usr/bin/env python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///usersCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

user1 = User(name="Thomas Ehmann", email="ehmannth@gmail.com")
session.add(user1)
session.commit()

myFirstCategory = Category(user_id=1, name="NBA Champions")
session.add(myFirstCategory)
session.commit()

chicago = Item(user_id=1, name="Chicago Bulls 1998", description="MJ, Pip, The Worm, and The Croation Sensation. What a team!", category=myFirstCategory)
session.add(chicago)
session.commit()

gsw = Item(user_id=1, name="Golden State Warriors 2016", description="Steph Curry, KD, Greene, and Klay. They are already a dynasty!", category=myFirstCategory)
session.add(gsw)
session.commit()

pl = Category(user_id=1, name="Premierleague Champions")
session.add(pl)
session.commit()

manC = Item(user_id=1, name="Man City 2018", description="Guardiola!", category=pl)
session.add(manC)
session.commit()

print "Added some data."
