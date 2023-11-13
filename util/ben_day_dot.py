class BenDayDot():
    def __init__(self, diameter: int, center: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        self.diameter = diameter
        self.center = center
        self.color = tuple([int(color[0]), int(color[1]), int(color[2])])
