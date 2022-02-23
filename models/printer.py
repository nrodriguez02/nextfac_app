import uuid
from typing import Dict


from octorest import OctoRest
from common.Database import Database
import json
import datetime
import time
import concurrent.futures
import socket
from urllib.parse import urlparse


class Printer:
    collection = "printers"

    def __init__(self, name: str, url: str, apikey: str, server: bool = None, _id: str = None):
        self.server = server
        self.name = name
        self.url = url
        self.apikey = apikey
        self.collection = "printers"
        self._id = _id or uuid.uuid4().hex

    def json(self) -> Dict:
        return {
            "_id": self._id,
            "name": self.name,
            "url": self.url,
            "apikey": self.apikey,
            "server": self.server
        }

    def save_to_mongo(self):
        Database.update(self.collection, {"_id": self._id}, self.json())

    def remove_from_mongo(self):
        Database.remove(self.collection, {"_id": self._id})

    def check_socket(self):
        parse_url = urlparse(self.url)
        hostname = parse_url.hostname
        if parse_url.port is None:
            if parse_url.scheme == 'https':
                port = 443
            else:
                port = 80
        else:
            port = parse_url.port
        try:
            sock = socket.create_connection((hostname, port), timeout=2)
        except:
            return False
        else:
            return True

    def con(self):
        if self.check_socket():
            try:
                con = OctoRest(url=self.url, apikey=self.apikey)
            except Exception as e:
                return False
            else:
                return con
        else:
            return False

    def state(self):
        if isinstance(self.con(), bool):
            return False
        else:
            try:
                state = self.con().connection_info()['current']['state']
                error204 = "204 No Content"
                error400 = "400 Bad Request"
                error409 = "Error"
                error_closed = "Closed"
                if error_closed not in state and error204 not in state and error400 not in state and error409 not in state:
                    return True
            except Exception as e:
                return False

    def connect(self):
        if not self.state():
            try:
                con = self.con()
            except Exception as e:
                raise TypeError(e)
            else:
                con.connect()
                return True

    def start_job(self) -> bool:

        if self.get_flag_operational() or self.get_flag_ready():
            if self.con().start():
                return True

        if self.get_flag_paused():
            if self.con().resume():
                return True

        return False

    def pause_job(self) -> bool:
        if self.get_flag_printing():
            if self.con().pause():
                return True
        return False

    def stop_job(self) -> bool:
        if self.get_flag_printing() or self.get_flag_paused():
            if self.con().cancel():
                return True
        return False

    def get_parameters(self):
        if self.state():
            parameters = self.con().printer()
            return parameters
        else:
            return False

    def get_job_info(self):
        if self.state():
            job_info = self.con().job_info()
            return job_info
        else:
            return False

    def get_flag_cancelling(self):
        if self.get_parameters():
            if 'Cancelling' in self.get_parameters()['state']['text']:
                return True
        return False

    def get_flag_operational(self):
        if self.get_parameters():
            if 'Operational' in self.get_parameters()['state']['text']:
                return True
        return False

    def get_flag_paused(self):
        if self.get_parameters():
            if 'Paused' in self.get_parameters()['state']['text']:
                return True
        return False

    def get_flag_pausing(self):
        if self.get_parameters():
            if 'Pausing' in self.get_parameters()['state']['text']:
                return True
        return False

    def get_flag_printing(self):
        if self.get_parameters():
            if 'Printing' in self.get_parameters()['state']['text']:
                return True
        return False

    def get_flag_ready(self):
        if self.get_parameters():
            if 'Ready' in self.get_parameters()['state']['text']:
                return True
        return False

    @staticmethod
    def do_history(printer_id):
        self = Printer.get_by_id(printer_id)
        history = {
            "printer_id": self._id,
            "printer_name": self.name,
            "state": "inactive",
            "cor": "danger",
            "temperature": {
                "tool": 0,
                "bed": 0
            },
            "target": {
                "tool": 0,
                "bed": 0
            },
            "job": {
                "file_name": None,
                "estimatedPrintTime": 0,
                "lastPrintTime": 0,
                "filament_length": 0,
                "completion": '0%',
                "printTime": 0,
                "printTimeLeft": 0,
                "left_time": 0,
            }
        }

        parameters = self.get_parameters()
        if not isinstance(parameters, bool):

            # flags = parameters['state']['flags'] if 'flags' in parameters['state'] else False
            history['state'] = parameters['state']['text'] if 'text' in parameters['state'] else "inactive"

            if history['state'] == "Operational" or history['state'] == "Ready":
                history['cor'] = "success"
            if history['state'] == "Printing":
                history['cor'] = "primary"
            if history['state'] == "Pausing" or history['state'] == "Paused" or history['state'] == "Cancelling":
                history['cor'] = "warning"

            temps = parameters['temperature'] if 'temperature' in parameters else False
            if temps is not False:
                history['temperature']['tool'] = self.get_tool_temperature(temps) if self.get_tool_temperature(
                    temps) else 0
                history['temperature']['bed'] = self.get_bed_temperature(temps) if self.get_bed_temperature(
                    temps) else 0
                history['target']['tool'] = self.get_tool_target(temps) if self.get_tool_target(temps) else 0
                history['target']['bed'] = self.get_bed_target(temps) if self.get_bed_target(temps) else 0

            job_info = self.get_job_info()

            job = job_info['job'] if 'job' in job_info else False
            if job is not False:
                estimatedPrintTime = job['estimatedPrintTime'] if 'estimatedPrintTime' in job else 0
                history['job']['estimatedPrintTime'] = str(datetime.timedelta(seconds=estimatedPrintTime)).split('.')[
                    0] if estimatedPrintTime is not None else "00:00:00"
                # history['job']['filament_length'] = 0

            file = job_info['job']['file'] if 'file' in job_info['job'] else False
            if file is not False:
                history['job']['file_name'] = str(file['name']).split('.')[0] if file['name'] is not None else "Unknown"

            progress = job_info['progress'] if 'progress' in job_info else False
            if progress is not False:
                completion = progress['completion'] if 'completion' in progress else 0
                if completion is not None:
                    history['job']['completion'] = str(completion).split('.')[0] + "%"
                printtimeleft = progress['printTimeLeft'] if 'printTimeLeft' in progress else 0
                if printtimeleft is not None:
                    history['job']['left_time'] = printtimeleft

                printTime = progress['printTime'] if 'printTime' in progress else 0
                history['job']['printTime'] = str(datetime.timedelta(seconds=printTime)).split('.')[
                    0] if printTime is not None else "00:00:00"

                PrintTimeLeft = progress['printTimeLeft'] if 'printTimeLeft' in progress else 0
                history['job']['printTimeLeft'] = str(datetime.timedelta(seconds=PrintTimeLeft)).split('.')[
                    0] if PrintTimeLeft is not None else "00:00:00"

            last_job = job_info['lastPrintTime'] if 'lastPrintTime' in job_info else False
            if last_job is not False:
                history['job']['lastPrintTime'] = str(datetime.timedelta(seconds=last_job)).split('.')[
                    0] if last_job is not None else "00:00:00"

        return history

    @staticmethod
    def history_threads():
        history = []
        ptime = 0
        printers = Printer.all()

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            future = [executor.submit(Printer.do_history, printer._id) for printer in printers]

            for f in concurrent.futures.as_completed(future, timeout=60):
                result = f.result()
                if result['job']['left_time'] > ptime:
                    ptime = result['job']['left_time']

                history.append(result)

        left_time = ptime * 1000
        return history, left_time

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
        result = Database.find("printers", {}).sort("name").skip(skip).limit(limit)
        return [cls(**printer) for printer in result] if result else None

    @classmethod
    def get_by_search(cls, parameter):
        result = Database.DATABASE[cls.collection].find(
            {"$or":
                [
                    {"name": {"$regex": parameter, "$options": 'i'}},
                    {"url": {"$regex": parameter, "$options": 'i'}}
                ]
            })
        return [cls(**elem) for elem in result] if result else None

    @staticmethod
    def heat(printer_id):
        printer = Printer.find_one_by("_id", printer_id)
        con = printer.con()
        if printer.state():
            try:
                con.tool_target(215)
                return True
            except Exception:
                return False

    @staticmethod
    def get_bed_temperature(temps):
        if 'bed' in temps:
            return temps['bed']['actual']
        return False

    @staticmethod
    def get_bed_target(temps):
        if 'bed' in temps:
            return temps['bed']['target']
        return False

    @staticmethod
    def get_tool_temperature(temps):
        if 'tool0' in temps:
            return temps['tool0']['actual']
        return False

    @staticmethod
    def get_tool_target(temps):
        if 'tool0' in temps:
            return temps['tool0']['target']
        return False
