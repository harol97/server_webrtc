import math
from datetime import datetime, timedelta
from logging import info

from cv2.typing import MatLike
from pydantic import BaseModel, Field
from torch.cuda import is_available
from ultralytics import YOLO

from .coordenate import Coordenate
from .rect import Rect


class TrackEntity(BaseModel):
    track_id: int
    name: str
    speed: float
    angle_degree: float
    rect: Rect
    datetime_detection: datetime = Field(default_factory=datetime.now)


class Tracker:
    def __init__(self, model="yolo11n.pt") -> None:
        self.yolov = YOLO(model)
        message_cuda_is_available = "is" if is_available else "is not"
        info(message_cuda_is_available, "using CUDA")
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
            rect = Rect(coord1=coord1, coord2=coord2)
            center = rect.center()
            current_time = datetime.now()
            if data_speed and current_time - data_speed[0] >= timedelta(seconds=1):
                first_point = data_speed[1]
                first_time = data_speed[0]
                rect_from_center = Rect(coord1=first_point, coord2=center)
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
                    name=result.names.get(cls, ""),
                    speed=speed,
                    angle_degree=angle,
                    rect=rect,
                )
            )
        return entities
