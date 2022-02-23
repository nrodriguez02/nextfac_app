from datetime import datetime
import uuid
from typing import Dict

from octorest import OctoRest

from common.Database import Database
from models.filament import Filament
from models.printer import Printer
from models.project import Project
from models.shift import Shift


class Job:
    collection = "jobs"

    def __init__(self, date: datetime, order_id: str, shift_id: str, printer_id: str, project_id: str, filament_id: str,
                 obs: str, status: bool, _id: str = None, insert_time: datetime = None):
        self.date = date
        self.order_id = order_id
        self.shift_id = shift_id
        self.printer_id = printer_id
        self.project_id = project_id
        self.filament_id = filament_id
        self.obs = obs
        self.status = status
        self.shift = None if self.shift_id is None else Shift.get_by_id(self.shift_id)
        self.printer = None if self.printer_id is None else Printer.get_by_id(self.printer_id)
        self.project = None if self.project_id is None else Project.get_by_id(self.project_id)
        self.filament = None if self.filament_id is None else Filament.get_by_id(self.filament_id)
        self.collection = "jobs"
        self._id = _id or uuid.uuid4().hex
        self.insert_time = insert_time or datetime.now()

    def json(self) -> Dict:
        return {
            "_id": self._id,
            "date": self.date,
            "order_id": self.order_id,
            "shift_id": self.shift_id,
            "printer_id": self.printer_id,
            "project_id": self.project_id,
            "filament_id": self.filament_id,
            "obs": self.obs,
            "status": self.status,
            "insert_time": self.insert_time
        }

    def con(self):
        try:
            con = OctoRest(url=self.printer.url, apikey=self.printer.apikey)
            return con
        except Exception as e:
            raise TypeError(e)

    @staticmethod
    def check_status(con):
        if con.state() != 'Operational':
            raise TypeError(con.state())
        else:
            return True

    @staticmethod
    def file_exist(con, file):
        try:
            con.select(file)
            return True
        except Exception:
            raise TypeError("File not found!")

    @staticmethod
    def clean_all(con):
        if con.files() is not None:
            try:
                con.delete(location='local/*')
                return True
            except Exception:
                raise TypeError("Error: Can't delete the files")
        else:
            return True

    def print(self):
        printer = self.con()
        ext = '.gcode'
        file = self.project.name + ext
        check_status = self.check_status(printer)
        if not check_status:
            return check_status
        self.clean_all(printer)
        printer.upload(self.project.path)
        file_exist = self.file_exist(printer, file)
        if not file_exist:
            return file_exist
        start = printer.start()
        if start is not None:
            raise TypeError(start)
        return None

    def save_to_mongo(self):
        Database.update(self.collection, {"_id": self._id}, self.json())

    def remove_from_mongo(self):
        Database.remove(self.collection, {"_id": self._id})

    def job_exist(self):
        result = Database.find_one(self.collection,
                                   {'date': self.date, 'shift_id': self.shift_id, 'printer_id': self.printer_id})
        if result is not None:
            return True

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
    def find_many_by_date_shift(cls, date, shift_id):
        result = Database.find(cls.collection, {'date': date, 'shift_id': shift_id})
        return [cls(**elem) for elem in result] if result else None

    @classmethod
    def all(cls):
        result = Database.find("jobs", {})
        return [cls(**job) for job in result] if result else None

    @classmethod
    def groupby(cls):
        result = Database.DATABASE[cls.collection].aggregate(
            [
                {"$lookup": {
                    "from": "shifts",
                    "localField": "shift_id",
                    "foreignField": "_id",
                    "as": "fromshifts"
                }},
                {"$lookup": {
                    "from": "projects",
                    "localField": "project_id",
                    "foreignField": "_id",
                    "as": "fromprojects"
                }},
                {"$lookup": {
                    "from": "printers",
                    "localField": "printer_id",
                    "foreignField": "_id",
                    "as": "fromprinters"
                }},
                {"$lookup": {
                    "from": "filaments",
                    "localField": "filament_id",
                    "foreignField": "_id",
                    "as": "fromfilaments"
                }},

                {"$group": {
                    "_id": {"date": "$date", "shift": ["$fromshifts._id", "$fromshifts.desc"]},
                    "jobs": {"$push": "$_id"},
                    "orders": {"$push": "$order_id"},
                    "printers": {"$push": "$fromprinters.name"},
                    "projects": {"$push": "$fromprojects.name"},
                    "filaments": {"$push": "$fromfilaments.name"},
                    "list_status": {"$push": "$status"},
                    "list_obs": {"$push": "$obs"}
                }},

                {"$sort": {"_id.date": -1, "_id.shift": 1}}
            ])
        return result

    @classmethod
    def jobs_amount(cls):
        results = Database.DATABASE[cls.collection].aggregate(
            [
                {"$lookup": {
                    "from": "shifts",
                    "localField": "shift_id",
                    "foreignField": "_id",
                    "as": "fromshifts"
                }},
                {"$group": {
                    "_id": {"date": "$date", "shift": ["$fromshifts._id", "$fromshifts.desc"]},

                }},

                {"$sort": {"_id.date": -1, "_id.shift": 1}}
            ])

        counter = 0
        for result in results:
            counter = counter + 1

        return counter

    @staticmethod
    def start_all(date, shift_id):
        disconnected_list = []
        jobs = Job.find_many_by_date_shift(date, shift_id)
        for job in jobs:
            if job.status is True:
                try:
                    job.print()
                except Exception as e:
                    if e.args[0] != "Printing":
                        disconnected_list.append([{"job_date": job.date, "job_shift": job.shift_id, "job_id": job._id,
                                                   "project_id": job.project_id, "job_name": job.project.name,
                                                   "printer_id": job.printer_id, "printer_name": job.printer.name,
                                                   "printer_url": job.printer.url, "error": e.args[0]}])
        return disconnected_list

    @staticmethod
    def connect_all(date, shift_id):
        disconnected_list = []
        jobs = Job.find_many_by_date_shift(date, shift_id)
        for job in jobs:
            if job.status is True:
                con = OctoRest(url=job.printer.url, apikey=job.printer.apikey)
                if con.state() != "Printing":
                    try:
                        job.printer.connect()
                        disconnected_list.append([{"job_date": job.date, "job_shift": job.shift_id, "job_id": job._id,
                                                   "project_id": job.project_id, "job_name": job.project.name,
                                                   "printer_id": job.printer_id, "printer_name": job.printer.name,
                                                   "printer_url": job.printer.url, "error": con.state()}])
                    except Exception as e:
                        disconnected_list.append([{"job_date": job.date, "job_shift": job.shift_id, "job_id": job._id,
                                                   "project_id": job.project_id, "job_name": job.project.name,
                                                   "printer_id": job.printer_id, "printer_name": job.printer.name,
                                                   "printer_url": job.printer.url, "error": e.args[0]}])
        return disconnected_list

    @staticmethod
    def start_one(job_id):
        job = Job.find_one_by("_id", job_id)
        if job.status is True:
            job.print()
            return True
        return False

    @classmethod
    def get_latest_jobs(cls):
        result = Database.find(cls.collection, {}).sort("insert_time", -1).limit(1)
        last_job = [cls(**job) for job in result]

        latest_jobs = Database.DATABASE[cls.collection].aggregate(
            [
                {"$match": {
                    "date": last_job[0].date,
                    "shift_id": last_job[0].shift_id
                }},

                {"$lookup": {
                    "from": "printers",
                    "localField": "printer_id",
                    "foreignField": "_id",
                    "as": "fromprinters"
                }},

                {"$lookup": {
                    "from": "filaments",
                    "localField": "filament_id",
                    "foreignField": "_id",
                    "as": "fromfilaments"
                }},

                {"$sort": {"fromprinters.name": 1}}
            ])

        return list(latest_jobs)

    @classmethod
    def get_by_search(cls, parameter):
        result = Database.DATABASE[cls.collection].find(
            {"$or":
                [
                    {"date": {"$regex": parameter, "$options": 'i'}},
                    {"order_id": {"$regex": parameter, "$options": 'i'}}
                ]
            })

        return [cls(**elem) for elem in result] if result else None

    @classmethod
    def search_amount(cls, parameter):
        results = Database.DATABASE[cls.collection].aggregate(
            [
                {"$lookup": {
                    "from": "shifts",
                    "localField": "shift_id",
                    "foreignField": "_id",
                    "as": "fromshifts"
                }},
                {"$match": {"$or":
                    [
                        {"date": {"$regex": parameter, "$options": 'i'}},
                        {"order_id": {"$regex": parameter, "$options": 'i'}}
                    ]
                }},
                {"$group": {
                    "_id": {"date": "$date", "shift": ["$fromshifts._id", "$fromshifts.desc"]},

                }},

                {"$sort": {"_id.date": -1, "_id.shift": 1}}
            ])

        counter = 0
        for result in results:
            counter = counter + 1

        return counter
