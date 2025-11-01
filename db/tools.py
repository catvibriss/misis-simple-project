import sqlalchemy as sql
import sqlalchemy.orm as orm
from . import structure
import random
from datetime import datetime

class Users:
    def __init__(self):
        pass
    
    def get(self, username: str = None, email: str = None) -> structure.User | Exception:
        session = structure.session
        try:
            if username:
                db = session.query(structure.User).filter(structure.User.username == username).one()
            elif email:
                db = session.query(structure.User).filter(structure.User.email == email).one()
            return db
        except Exception as e:
            return e
        
    def update(self, new_db: structure.User) -> None:
        session = structure.session
        session.add(new_db)
        session.commit()
        
    def register(self, username: str, password: str, email: str) -> Exception | structure.User:
        session = structure.session
        exu = structure.User(username=username, email=email, password=password)
        try:
            session.add(exu)
            session.commit()
        except Exception as e:
            session.rollback()
            return e
        return exu
    
    def get_token(self, user: structure.User, reset_old: bool = False) -> structure.Token | Exception:
        session = structure.session
        try: 
            if reset_old:
                session.query(structure.Token).filter(structure.Token.user_id == user.id).delete()
            tokens: list[structure.Token] = session.query(structure.Token).filter(structure.Token.user_id == user.id, structure.Token.is_active == True, structure.Token.expires_at > datetime.now()).all()
            if len(tokens) != 0:
                return random.choice(tokens)
            new_token = structure.Token(user_id=user.id)
            session.add(new_token)
            session.commit()
            return new_token
        except Exception as e:
            session.rollback()
            return e