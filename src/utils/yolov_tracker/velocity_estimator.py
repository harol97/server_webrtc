import math
from datetime import datetime, timedelta

from pydantic import BaseModel

from src.utils.yolov_tracker.coordenate import Coordenate
from src.utils.yolov_tracker.rect import Rect


class Velocity(BaseModel):
    speed: float
    angle: float


class VelocityEstimator:
    def __init__(self) -> None:
        self.speeds_tracks: dict[int, tuple[datetime, Coordenate, Velocity]] = {}

    def estimate_velocity(self, track_id: int, center: Coordenate) -> Velocity:
        data = self.speeds_tracks.get(track_id)
        if not data:
            velocity = Velocity(speed=0.0, angle=0.0)
            self.speeds_tracks[track_id] = (datetime.now(), center, velocity)
            return velocity
        current_time = datetime.now()
        if current_time - data[0] < timedelta(seconds=1):
            return data[2]
        first_point = data[1]
        first_time = data[0]
        rect_from_center = Rect(coord1=first_point, coord2=center)
        time_in_seconds = (current_time - first_time).total_seconds()
        speed = int(rect_from_center.distance() / time_in_seconds)
        angle_degree = 0
        if rect_from_center.can_calculate_slop():
            angle = math.atan2(center.y - first_point.y, center.x - first_point.x)
            angle_degree = math.degrees(angle)
        velocity = Velocity(speed=speed, angle=angle_degree)
        self.speeds_tracks[track_id] = (datetime.now(), center, velocity)
        return velocity
