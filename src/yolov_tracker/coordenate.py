from dataclasses import asdict, dataclass


@dataclass
class Coordenate:
    x: int
    y: int

    def as_tuple(self, offset_x=0, offset_y=0):
        return (self.x + offset_x, self.y + offset_y)

    def as_dict(self):
        return asdict(self)
