import math

from cv2 import arrowedLine, putText, rectangle
from cv2.typing import MatLike

from .tracker_manager import TrackEntity


class Drawer:
    def draw(self, frame: MatLike, detections: list[TrackEntity]) -> MatLike:
        new_frame = frame.copy()
        color = (19, 19, 242)
        for detection in detections:
            distance = detection.rect.distance() / 2
            angle_rad = math.radians(detection.angle_degree)
            if distance != 0 and detection.angle_degree != 0:
                x, y = (
                    detection.center.x + distance * math.cos(angle_rad),
                    detection.center.y - distance * math.sin(angle_rad),
                )
                arrowedLine(
                    new_frame,
                    detection.center.as_tuple(),
                    (int(x), int(y)),
                    color,
                    2,
                )
            putText(
                new_frame,
                f"{detection.track_id}-sd: {detection.speed:.1f}-ag: {detection.angle_degree:.1f}",
                detection.coordenate_1.as_tuple(offset_y=-5),
                1,
                1.5,
                color,
                2,
            )
            rectangle(
                new_frame,
                detection.coordenate_1.as_tuple(),
                detection.coordenate_2.as_tuple(),
                color,
                2,
                2,
            )
        return new_frame
