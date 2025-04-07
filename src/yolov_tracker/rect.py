import math

from .coordenate import Coordenate


class Rect:
    def __init__(self, coord1: Coordenate, coord2: Coordenate) -> None:
        self.coord1 = coord1
        self.coord2 = coord2

    def distance(self) -> float:
        return math.sqrt(
            math.pow(self.coord1.x - self.coord2.x, 2)
            + math.pow(self.coord1.y - self.coord2.y, 2)
        )

    def center(self) -> Coordenate:
        return Coordenate(
            int((self.coord1.x + self.coord2.x) / 2),
            int((self.coord1.y + self.coord2.y) / 2),
        )

    def can_calculate_slop(self) -> int:
        return self.coord2.x - self.coord1.x

    def slop(self) -> float:
        return (self.coord2.y - self.coord1.y) / (self.coord2.x - self.coord1.x)

    @staticmethod
    def distance_between_two_points(coord1: Coordenate, coord2: Coordenate) -> float:
        return math.sqrt(
            math.pow(coord1.x - coord2.x, 2) + math.pow(coord1.y - coord2.y, 2)
        )
