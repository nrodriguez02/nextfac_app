import datetime
import uuid
from typing import Dict

from common.Database import Database


class Project:
    collection = "projects"

    def __init__(self, name: str, time: datetime, weight: float, path: str, _id: str = None):
        self.name = name
        self.time = time
        self.weight = weight
        self.path = path
        self.collection = "projects"
        self._id = _id or uuid.uuid4().hex

    def json(self) -> Dict:
        return {
            "_id": self._id,
            "name": self.name,
            "time": self.time,
            "weight": self.weight,
            "path": self.path
        }

    def save_to_mongo(self):
        Database.update(self.collection, {"_id": self._id}, self.json())

    def remove_from_mongo(self):
        Database.remove(self.collection, {"_id": self._id})

    @classmethod
    def find_one_by(cls, attribute, value):
        result = Database.find_one(cls.collection, {attribute: value})
        return cls(**result) if result else None

    @classmethod
    def find_many_by(cls, attribute, value):
        result = Database.find(cls.collection, {attribute: value})
        return [cls(**elem) for elem in result] if result else None

    @classmethod
    def get_by_id(cls, _id):
        return cls.find_one_by("_id", _id)

    @classmethod
    def all(cls, skip=0, limit=0):
        result = Database.find("projects", {}).sort("name").skip(skip).limit(limit)
        return [cls(**project) for project in result] if result else None

    @classmethod
    def get_by_search(cls, parameter):
        result = Database.DATABASE[cls.collection].find(
            {"$or":
                [
                    {"name": {"$regex": parameter, "$options": 'i'}},
                    {"path": {"$regex": parameter, "$options": 'i'}}
                ]
            })
        return [cls(**elem) for elem in result] if result else None
