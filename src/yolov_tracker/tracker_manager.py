import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cv2.typing import MatLike
from ultralytics import YOLO

from .coordenate import Coordenate
from .rect import Rect


@dataclass
class TrackEntity:
    track_id: int
    coordenate_1: Coordenate
    coordenate_2: Coordenate
    frame: MatLike
    name: str
    speed: float
    angle_degree: float
    center: Coordenate
    rect: Rect
    datetime_detection: datetime = field(default_factory=datetime.now)

    def model_dump(self):
        return {
            "trackId": self.track_id,
            "coordenate1": self.coordenate_1.as_dict(),
            "coordenate2": self.coordenate_2.as_dict(),
            "name": self.name,
            "speed": self.speed,
            "angle_degree": self.angle_degree,
            "center": self.center.as_dict(),
            "datetime_detection": self.datetime_detection.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def as_string(self):
        return json.dumps(self.model_dump())


class Tracker:
    def __init__(self, model="yolo11n.pt") -> None:
        self.yolov = YOLO(model)
        self.speeds_tracks: dict[int, tuple[datetime, Coordenate, float, float]] = {}

    def get_tracks(self, from_frame: MatLike) -> list[TrackEntity]:
        frame = from_frame.copy()
        entities = []
        results = self.yolov.track(
            frame,
            persist=True,
            verbose=False,
            show=False,
            tracker="bytetrack.yaml",
            classes=[0],
        )
        if not results:
            return []
        result = results[0]
        if result.boxes is None:
            return []
        if result.boxes.id is None:
            return []
        for box, tensor_track_id, cls in zip(
            result.boxes.xyxy, result.boxes.id, result.boxes.cls
        ):
            cls = int(cls)
            x1, y1, x2, y2 = box
            track_id = int(tensor_track_id)
            coord1 = Coordenate(x=int(x1.round()), y=int(y1.round()))
            coord2 = Coordenate(x=int(x2.round()), y=int(y2.round()))
            data_speed = self.speeds_tracks.get(track_id)
            speed = 0
            rect = Rect(coord1, coord2)
            center = rect.center()
            current_time = datetime.now()
            if data_speed and current_time - data_speed[0] >= timedelta(seconds=1):
                first_point = data_speed[1]
                first_time = data_speed[0]
                rect_from_center = Rect(first_point, center)
                time_in_seconds = (current_time - first_time).total_seconds()
                speed = int(rect_from_center.distance() / time_in_seconds)
                angle_degree = 0
                if rect_from_center.can_calculate_slop():
                    angle = math.atan2(
                        center.y - first_point.y, center.x - first_point.x
                    )
                    angle_degree = math.degrees(angle)
                self.speeds_tracks[track_id] = (
                    datetime.now(),
                    center,
                    speed,
                    angle_degree,
                )
            if not data_speed:
                data_speed = (datetime.now(), center, 0, 0)
                self.speeds_tracks[track_id] = data_speed
            speed = data_speed[2]
            angle = data_speed[3]
            entities.append(
                TrackEntity(
                    track_id=track_id,
                    coordenate_1=coord1,
                    coordenate_2=coord2,
                    frame=frame[coord1.x : coord2.x, coord1.y : coord2.y],
                    name=result.names.get(cls, ""),
                    speed=speed,
                    angle_degree=angle,
                    center=center,
                    rect=rect,
                )
            )
        return entities
