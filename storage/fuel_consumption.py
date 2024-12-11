from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql.functions import now
from base import Base
import datetime

class FuelConsumption(Base):
    """ Fuel Consumption """

    __tablename__ = "fuel_consumption"

    id = Column(Integer, primary_key=True)
    vessel_id = Column(String(250), nullable=False)
    device_id = Column(Integer, nullable=False)
    fuel_consumed = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)

    def __init__(self, vessel_id, device_id, fuel_consumed, timestamp, trace_id):
        self.vessel_id = vessel_id
        self.device_id = device_id
        self.fuel_consumed = fuel_consumed
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now()
        self.trace_id = trace_id

    def to_dict(self):
        new_dict = {}
        new_dict['id'] = self.id
        new_dict['vessel_id'] = self.vessel_id
        new_dict['device_id'] = self.device_id
        new_dict['fuel_consumed'] = self.fuel_consumed
        new_dict['timestamp'] = self.timestamp
        new_dict['date_created'] = self.date_created
        new_dict['trace_id'] = self.trace_id

        return new_dict

