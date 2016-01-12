from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Boolean, Integer, String, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import UniqueConstraint

from datetime import datetime
from os.path import expanduser


Base = declarative_base()


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    telegram_id = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    known = Column(Boolean, default=False)

    def __repr__(self):
        return "<User(first_name='%s', last_name='%s', telegram_id='%d', known='%d')>" % (self.first_name, self.last_name, self.telegram_id, self.known)


class Url(Base):

    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, nullable=False)
    location = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return "<Url('%s')>" % (self.location)


class Subscription(Base):

    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    query_period = Column(Integer, nullable=False)
    query_deviation = Column(Integer, default=0)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)
    last_query = Column(DateTime)

    def __repr__(self):
        return "<Subscription(user_id='%s')>" % (self.user_id)


class SentOffer(Base):

    __tablename__ = 'sent_offers'
    __table_args__ = (UniqueConstraint('user_id', 'url_id'),)

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)


class WNDB(object):

    def __init__(self, path):
        self.engine = create_engine('sqlite:///' + path, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)

    def getSession(self):
        return self.Session()


def main():
    db = WNDB(path='/tmp/wn.sqlite')
    session = db.getSession()
    try:
        telegram_user = User(first_name="Some", last_name="One", telegram_id = 9999)
        session.add(telegram_user)
        welds = Url(
            location='http://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?ELECTROTOOLS_DETAIL=15&areaId=3&CATEGORY%2FMAINCATEGORY=8210&CATEGORY%2FSUBCATEGORY=8326&PRICE_FROM=0&PRICE_TO=300')
        session.add(welds)
        session.flush()
        subscription = Subscription(
            user_id=telegram_user.id,
            query_period=3600,
            url_id=welds.id)
        session.add(subscription)
        for user in session.query(User).filter(User.first_name=='Some'):
            print(user)
        for subscription in session.query(Subscription):
            subscription.lastquery = datetime.now()

        #sent = SentOffer(user_id=telegram_user.id, url_id=0)
        #session.add(sent)

        #raise Exception("Prevent commit.")

        print("Committing session.")
        session.commit()
    except Exception as exc:
        print(exc)
        session.rollback()
    finally:
        print("Closing session.")
        session.close()

    session = db.getSession()
    for user, subscription, url in \
        session.query(User, Subscription, Url).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id).all():
        print(user.first_name + ", " + user.last_name + ", " + url.location)

if __name__ == "__main__":
    main()
