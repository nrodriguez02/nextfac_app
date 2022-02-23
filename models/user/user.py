import uuid

from datetime import datetime
from typing import Dict, List

from common.Database import Database
from common.utils import Utils
import models.user.errors as UserErrors


class User:
    collection = "users"

    def __init__(self, name: str, area: str, email: str, password: str, group_id: str, creation_date: str = None,_id: str = None):
        self.name = name
        self.area = area
        self.email = email
        self.password = password
        self.group_id = group_id
        self.creation_date = creation_date or datetime.now()
        self.collection = "users"
        self._id = _id or uuid.uuid4().hex

    def json(self) -> Dict:
        return {
            "_id": self._id,
            "name": self.name,
            "area": self.area,
            "email": self.email,
            "password": self.password,
            "group_id": self.group_id,
            "creation_date": self.creation_date
        }

    def save_to_mongo(self):
        Database.update(self.collection, {"_id": self._id}, self.json())

    def remove_from_mongo(self):
        Database.remove(self.collection, {"_id": self._id})

    @classmethod
    def find_one_by(cls, attribute, value):
        return cls(**Database.find_one(cls.collection, {attribute: value}))

    @classmethod
    def find_many_by(cls, attribute, value):
        return [cls(**elem) for elem in Database.find(cls.collection, {attribute: value})]

    @classmethod
    def get_by_id(cls, _id):
        return cls.find_one_by("_id", _id)

    @classmethod
    def all(cls, skip=0, limit=0):
        return [cls(**user) for user in Database.find("users", {}).sort("name").skip(skip).limit(limit)]

    @classmethod
    def get_by_search(cls, parameter):
        results = Database.DATABASE[cls.collection].find(
            {"$or":
                [
                    {"name": {"$regex": parameter, "$options": 'i'}},
                    {"email": {"$regex": parameter, "$options": 'i'}},
                    {"area": {"$regex": parameter, "$options": 'i'}}
                ]
            })
        return [cls(**elem) for elem in results]

    @classmethod
    def find_by_email(cls, email: str):
        try:
            return cls.find_one_by('email', email)
        except TypeError:
            raise UserErrors.UserNotFoundError('User e-mail not found.')

    @classmethod
    def register_user(cls, email: str, password: str, name: str, area: str, group_id: str) -> bool:
        if not Utils.email_is_valid(email):
            raise UserErrors.InvalidEmailError('The e-mail does not have the right format.')

        try:
            cls.find_by_email(email)
            raise UserErrors.UserAlreadyRegisteredError('The email you used to register already exists.')
        except UserErrors.UserNotFoundError:
            User(name, area, email, Utils.hash_password(password), group_id).save_to_mongo()

        return True

    @classmethod
    def is_login_valid(cls, email: str, password: str) -> bool:
        user = cls.find_by_email(email)

        if not Utils.check_hashed_password(password, user.password):
            raise UserErrors.IncorrectPasswordError('Wrong password, please try again!')

        return True
