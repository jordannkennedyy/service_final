from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql.functions import now
from base import Base
import datetime


class TorqueReading(Base):
    """ Torque Reading """

    __tablename__ = "torque_reading"

    id = Column(Integer, primary_key=True)
    vessel_id = Column(String(250), nullable=False)
    device_id = Column(Integer, nullable=False)
    torque = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)

    def __init__(self, vessel_id, device_id, torque, timestamp, trace_id):
        self.vessel_id = vessel_id
        self.device_id = device_id
        self.torque = torque
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now()
        self.trace_id = trace_id

    def to_dict(self):
        new_dict = {}
        new_dict['id'] = self.id
        new_dict['vessel_id'] = self.vessel_id
        new_dict['device_id'] = self.device_id
        new_dict['torque'] = self.torque
        new_dict['timestamp'] = self.timestamp
        new_dict['date_created'] = self.date_created
        new_dict['trace_id'] = self.trace_id

        return new_dict