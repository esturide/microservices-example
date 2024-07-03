import abc
import dataclasses
import datetime
import hashlib

import bcrypt
import tinydb


def generate_salt() -> str:
    return bcrypt.gensalt().decode('utf-8')


def generate_token() -> str:
    return bcrypt.gensalt().decode('utf-8')


def create_salt_password(salt: str, password: str) -> str:
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


class UserDataModel:
    @staticmethod
    def create(*args, **kwargs): ...

    @staticmethod
    def load(db: tinydb.TinyDB, username: str): ...

    @abc.abstractmethod
    def search(self, db: tinydb.TinyDB): ...

    @abc.abstractmethod
    def save(self, db: tinydb.TinyDB): ...

    @property
    @abc.abstractmethod
    def json(self): ...


@dataclasses.dataclass
class UserModel(UserDataModel):
    username: str
    salt: str
    __password: str | None = None
    __salt_password: str | None = None

    @property
    def encrypt_model(self):
        return self.__password is None

    @property
    def salt_password(self):
        if not self.encrypt_model:
            return create_salt_password(self.salt, self.__password)

        return self.__salt_password

    @staticmethod
    def create(_dict: dict):
        try:
            return UserModel(
                _dict['username'],
                generate_salt(),
                _dict.get('password', None)
            )
        except TypeError:
            return None

    @staticmethod
    def load(db: tinydb.TinyDB, username: str):
        user_query = tinydb.Query()
        query = db.search(user_query['username'] == username)

        if len(query) <= 0:
            return None

        query = query[0]

        try:
            return UserModel(
                query['username'],
                query['salt'],
                None,
                query['password']
            )
        except TypeError:
            return None

    def search(self, db: tinydb.TinyDB):
        user_query = tinydb.Query()
        query = db.search(user_query['username'] == self.username)

        if len(query) <= 0:
            return None

        return query[0]

    def save(self, db: tinydb.TinyDB):
        db.insert({
            'username': self.username,
            'salt': self.salt,
            'password': self.salt_password
        })

    def validate_password(self, user_db):
        salt_password_ = create_salt_password(
            user_db.salt,
            self.__password
        )

        return salt_password_ == user_db.salt_password

    @property
    def json(self):
        return {
            'username': self.username,
        }


@dataclasses.dataclass
class TokenModel(UserDataModel):
    username: str
    token: str
    time: datetime.datetime

    @staticmethod
    def create(username: str):
        return TokenModel(
            username,
            generate_token(),
            datetime.datetime.now()
        )

    @staticmethod
    def load(db: tinydb.TinyDB, username: str):
        token_query = tinydb.Query()
        query = db.search(token_query['username'] == username)

        if len(query) <= 0:
            return None

        query = query[0]
        return TokenModel(**query)

    def search(self, db: tinydb.TinyDB):
        user_query = tinydb.Query()
        query = db.search(user_query['username'] == self.username)

        if len(query) <= 0:
            return None

        return query[0]

    def save(self, db: tinydb.TinyDB):
        db.insert({
            'username': self.username,
            'token': self.token,
            'time': int(self.time.timestamp())
        })

    @property
    def json(self):
        return {
            'username': self.username,
            'token': self.token,
            'time': self.time.timestamp(),
        }
