import sqlalchemy as sql
import sqlalchemy.orm as orm
from . import structure

class Users:
    def __init__(self):
        pass
    
    def get_database(self, username: str = None, email: str = None) -> structure.User | Exception:
        session = structure.session
        try:
            if username:
                db = session.query(structure.User).filter(structure.User.username == username).one()
            elif email:
                db = session.query(structure.User).filter(structure.User.email == email).one()
            return db
        except Exception as e:
            return e
        
    def save_database(self, new_db: structure.User) -> None:
        session = structure.session
        session.add(new_db)
        session.commit()
        
    def register_user(self, username: str, password: str, email: str) -> Exception | structure.User:
        session = structure.session
        exu = structure.User(username=username, email=email, password=password)
        try:
            session.add(exu)
            session.commit()
        except Exception as e:
            session.rollback()
            return e
        return exu