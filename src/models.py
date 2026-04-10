from dataclasses import dataclass


@dataclass
class Question:
    id: int
    image_url: str
    answer_hash: str
    category: str
    image_filename: str = ""
    image_query: str = ""
    answer_mask: str = "**********"
    answer_length: int = 10
    answer_enc: str = ""


class GridCell:
    def __init__(self, index: int, grid_size: int):
        self.index = index
        self.row = index // grid_size
        self.col = index % grid_size

    def get_bounds(self, cell_pixel_size: int) -> tuple:
        x1 = self.col * cell_pixel_size
        y1 = self.row * cell_pixel_size
        return (x1, y1, x1 + cell_pixel_size, y1 + cell_pixel_size)

    @staticmethod
    def get_cell_from_click(click_x: int, click_y: int, grid_size: int, img_w: int, img_h: int) -> int:
        if img_w <= 0 or img_h <= 0:
            return -1
        col = max(0, min(int(click_x / (img_w / grid_size)), grid_size - 1))
        row = max(0, min(int(click_y / (img_h / grid_size)), grid_size - 1))
        return row * grid_size + col
