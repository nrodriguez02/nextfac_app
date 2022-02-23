import math
import re
import datetime

from flask import session
from passlib.hash import pbkdf2_sha512


class Utils:
    @staticmethod
    def email_is_valid(email: str) -> bool:
        email_address_matcher = re.compile(r'^[\w-]+@([\w-]+\.)+[\w-]+$')
        return True if email_address_matcher.match(email) else False

    @staticmethod
    def hash_password(password: str) -> str:
        return pbkdf2_sha512.encrypt(password)

    @staticmethod
    def check_hashed_password(password: str, hashed_password: str) -> bool:
        return pbkdf2_sha512.verify(password, hashed_password)

    @staticmethod
    def make_session_permanent(status: bool) -> bool:
        session.permanent = status
        return True

    @staticmethod
    def get_print_time(filename):
        with open(filename, 'r') as f_gcode:
            data = f_gcode.read()
            re_value = re.search('Build time: .*', data)

            if re_value:
                value = str(re_value.group().split(': ')[1])
                value = re.sub('hours', 'hour', value)
                value = re.sub('minutes', 'minute', value)
                value = re.sub(' hour ', ':', value)
                value = re.sub(' minute', '', value)
                clean_time = value.split(':')
                if len(clean_time) > 1:
                    hours = float(clean_time[0])
                    minutes = float(clean_time[1])
                    strtotime = datetime.timedelta(hours=hours, minutes=minutes).total_seconds()
                if len(clean_time) == 1:
                    minutes = float(clean_time[0])
                    strtotime = datetime.timedelta(minutes=minutes).total_seconds()
                return strtotime
            else:
                value = 0
            return value

    @staticmethod
    def get_weight(filename):
        with open(filename, 'r') as f_gcode:
            data = f_gcode.read()
            re_value = re.search('Plastic weight: .\d.*.g', data)

            if re_value:
                value = str(re_value.group().split(': ')[1])
                clean_value = re.sub(' g', '', value)
                return clean_value
            else:
                value = '0'
            return value
