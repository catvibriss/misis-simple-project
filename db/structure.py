import sqlalchemy as sql
import sqlalchemy.orm as orm
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from hashlib import sha256

engine = sql.create_engine('sqlite:///database.db')
session = orm.Session(bind=engine)

Base = orm.declarative_base()
metadata: sql.MetaData = Base.metadata

class User(Base):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(sql.Integer, primary_key=True)
    registred_at: orm.Mapped[datetime] = orm.mapped_column(sql.DateTime(), default=datetime.now)

    username: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True)
    _email: orm.Mapped[str] = orm.mapped_column(sql.Text, nullable=False, unique=True, name="email")

    _password_hash: orm.Mapped[str] = orm.mapped_column(sql.String(64), nullable=False, name="password_hash")
    
    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if "@" not in value:
            raise ValueError("wrong email")
        self._email = value.lower()
    
    @hybrid_property
    def password(self):
        return self._password_hash
    
    @password.setter
    def password(self, value: str):
        '''
        value - password, NOT password hash
        '''
        self._password_hash = sha256(value.encode("utf-8")).hexdigest()
        
    def is_password(self, password_check: str):
        check_hash = sha256(password_check.encode("utf-8")).hexdigest()
        return check_hash == self._password_hash
    
metadata.create_all(engine)