from datetime import datetime
from logging import info

from cv2.typing import MatLike
from pydantic import BaseModel, Field
from torch.cuda import is_available
from ultralytics import YOLO

from .coordenate import Coordenate
from .rect import Rect
from .velocity_estimator import VelocityEstimator


class TrackEntity(BaseModel):
    track_id: int
    name: str
    speed: float
    angle_degree: float
    rect: Rect
    datetime_detection: datetime = Field(default_factory=datetime.now)


class Tracker:
    def __init__(
        self,
        conf: float,
        iou: float,
        model="yolo11n.pt",
    ) -> None:
        self.yolov = YOLO(model)
        self.velocityEstimator = VelocityEstimator()
        message_cuda_is_available = "It is" if is_available else "It isn't"
        info(message_cuda_is_available, "using CUDA")
        self.conf = conf
        self.iou = iou

    def get_tracks(self, from_frame: MatLike) -> list[TrackEntity]:
        frame = from_frame.copy()
        entities = []
        results = self.yolov.track(
            frame, persist=True, verbose=False, show=False, conf=self.conf, iou=self.iou
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
            rect = Rect(coord1=coord1, coord2=coord2)
            center = rect.center()
            velocity = self.velocityEstimator.estimate_velocity(track_id, center)
            entities.append(
                TrackEntity(
                    track_id=track_id,
                    name=result.names.get(cls, ""),
                    speed=velocity.speed,
                    angle_degree=velocity.angle,
                    rect=rect,
                )
            )
        return entities
