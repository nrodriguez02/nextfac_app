import datetime
import uuid
from typing import Dict

from common.Database import Database


class Shift:
    collection = "shifts"

    def __init__(self, desc: str, timein: datetime, timeout: datetime, _id: str = None):
        self.desc = desc
        self.timein = timein
        self.timeout = timeout
        self.collection = "shifts"
        self._id = _id or uuid.uuid4().hex

    def json(self) -> Dict:
        return {
            "_id": self._id,
            "desc": self.desc,
            "timein": self.timein,
            "timeout": self.timeout
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
        result = Database.find("shifts", {}).sort("desc").skip(skip).limit(limit)
        return [cls(**shift) for shift in result] if result else None

    @classmethod
    def get_by_search(cls, parameter):
        result = Database.DATABASE[cls.collection].find(
            {"$or":
                [
                    {"desc": {"$regex": parameter, "$options": 'i'}}
                ]
            })
        return [cls(**elem) for elem in result] if result else None
