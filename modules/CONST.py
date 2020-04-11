from .map import Map
from PyQt5.Qt import QFont

MAIN_UI_PATH = "application.ui"
SIZE_API = 650, 450

API_SEARCH_MAP = "https://search-maps.yandex.ru/v1/"
API_STATIC_MAP = "https://static-maps.yandex.ru/1.x/"
API_GEOSEARCH = "http://geocode-maps.yandex.ru/1.x/"

SEARCH_MAP_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
GEOSEARCH_KEY = "40d1649f-0493-4b70-98ba-98533de7710b"

START_PLACE = "проспект Aль-Фараби 77/8, Алматы"
START_POS = Map.get_obj_data(START_PLACE)[0]["pos"]
START_ZOOM = 17

MAP_TYPES = (
    ("Схема", "map"),
    ("Спутник", "sat"),
    ("Гибрид", "sat,skl")
)

MAP_TYPE_FONT = QFont("MS Shell Dlg 2", 12)

MIN_ZOOM = 0
MAX_ZOOM = 17
D_ZOOM = 1

MIN_LATITUDE = -180
MAX_LATITUDE = 180

MIN_LONGITUDE = -90
MAX_LONGITUDE = 90

MAP_POINT_SIZE = "l"  # s m l
TEXT_TO_FIND_CLOSE = "организация"
DELTA_TO_FIND = (1 / (111 * 10 ** 3)) * 50, (1 / (111 * 10 ** 3)) * 50

UP_SCALE = 1
DOWN_SCALE = 2

MOVE_UP = 3
MOVE_DOWN = 4
MOVE_LEFT = 5
MOVE_RIGHT = 6
