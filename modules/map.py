from . import CONST
import requests
import math


class ApiException(Exception):
    def __init__(self, msg):
        super(ApiException, self).__init__("Error: " + msg)


class Map:
    def __init__(self):
        self.map_type = CONST.MAP_TYPES[0][1]

        self.zoom = CONST.START_ZOOM
        self.position = CONST.START_POS

        self.points = list()
        self.points_data = list()

    @property
    def get_params_for_map(self) -> dict:
        default_params = {'l': self.map_type,
                          "ll": ','.join(str(i) for i in self.position),
                          "z": self.zoom,
                          "size": ','.join(str(i) for i in CONST.SIZE_API)}
        if len(self.points):
            default_params["pt"] = self.get_points()
        return default_params

    def get_map_bytes(self, params=None) -> bytes:
        if params is None:
            params = self.get_params_for_map
        r = requests.get(CONST.API_STATIC_MAP, params=params)
        if r.status_code != 200:
            msg = r.text.split('<message>')[1].split('</message>')[0]
            raise ApiException(msg)
        return r.content

    @staticmethod
    def get_obj_data(text_to_find, need_result=10, close_to_click=None):
        params = {
            "apikey": CONST.SEARCH_MAP_KEY,
            "text": text_to_find,
            "lang": "ru_RU",
            "results": need_result
        }
        if close_to_click is not None:
            lon, lat = close_to_click
            params = {**params,
                      'text': 'орган',
                      "type": 'biz',
                      "ll": f"{lon},{lat}",
                      "spn": f"{CONST.DELTA_TO_FIND[0]},{CONST.DELTA_TO_FIND[1]}",
                      "rspn": 1
                      }

        r = requests.get(CONST.API_SEARCH_MAP, params=params)
        if r.status_code != 200:
            raise ApiException(r.json()["message"])

        results = list()
        for obj in r.json()["features"]:
            obj_dict = dict()
            results.append(obj_dict)

            obj_properties = obj['properties']
            obj_dict["name"] = obj_properties['name']

            obj_dict["pos"] = obj['geometry']['coordinates']
            if "GeocoderMetaData" in obj_properties:
                if 'address' in obj_properties["GeocoderMetaData"]:
                    obj_dict["address"] = obj_properties["GeocoderMetaData"]["address"]
                elif 'text' in obj_properties["GeocoderMetaData"]:
                    obj_dict["address"] = obj_properties["GeocoderMetaData"]["text"]
            elif "CompanyMetaData" in obj_properties:
                if "address" in obj_properties["CompanyMetaData"]:
                    obj_dict["address"] = obj_properties["CompanyMetaData"]["address"]

            obj_dict["post_code"] = Map.get_postal_code(obj_dict["address"])
        if len(results):
            return results
        return None

    @staticmethod
    def get_postal_code(official_address):
        params = {
            "apikey": CONST.GEOSEARCH_KEY,
            'geocode': official_address,
            "format": "json"
        }
        r = requests.get(CONST.API_GEOSEARCH, params=params).json()
        try:
            return r["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
                "GeocoderMetaData"][
                "Address"]["postal_code"]
        except:
            return "не найдено"

    @property
    def get_delta_longitude_per_scale(self):
        # градус / пиксель
        temp = ((360 * 90) / (4 ** self.zoom)) ** 0.5 / CONST.SIZE_API[0]
        return temp * 10

    @property
    def get_delta_latitude_per_scale(self):
        temp = ((360 * 90) / (4 ** self.zoom)) ** 0.5 / CONST.SIZE_API[1]
        return temp * 10

    def setMapType(self, value):
        self.map_type = value

    def setScale(self, action):
        """
        Изменение маштаба
        """
        # PgUp = 4 and PgDown = 5
        if action == CONST.UP_SCALE:
            zoom = self.zoom + CONST.D_ZOOM
        elif action == CONST.DOWN_SCALE:
            zoom = self.zoom - CONST.D_ZOOM

        if CONST.MIN_ZOOM <= zoom <= CONST.MAX_ZOOM:
            self.zoom = zoom

    def move_on_map(self, action):
        """
        Перемещение по карте
        """
        longitude, latitude = self.position
        if action == CONST.MOVE_UP:
            latitude += self.get_delta_latitude_per_scale
        elif action == CONST.MOVE_DOWN:
            latitude -= self.get_delta_latitude_per_scale
        elif action == CONST.MOVE_LEFT:
            longitude -= self.get_delta_longitude_per_scale
        elif action == CONST.MOVE_RIGHT:
            longitude += self.get_delta_longitude_per_scale
        if self.check_coord((longitude, latitude)):
            self.position = longitude, latitude

    def check_coord(self, pos):
        longitude, latitude = pos
        if (CONST.MIN_LATITUDE <= latitude <= CONST.MAX_LATITUDE) and \
                (CONST.MIN_LONGITUDE <= longitude <= CONST.MAX_LONGITUDE):
            return True
        return False

    def set_center(self, point):
        self.position = point

    def clear_points(self):
        if len(self.points) == 0:
            return False
        self.points.clear()

    def add_point(self, pos, address, post_index):
        self.points.append(pos)
        self.points_data.append((address, post_index))

    def get_points(self):
        size = CONST.MAP_POINT_SIZE
        return '~'.join(f"{x},{y},pmwt{size}{i + 1}" for (x, y), i in zip(self.points, range(len(self.points))))

    def get_points_count(self):
        return len(self.points)

    @staticmethod
    def lonlat_distance(a, b):
        # Результат в метрах
        degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
        a_lon, a_lat = a
        b_lon, b_lat = b

        # Берем среднюю по широте точку и считаем коэффициент для нее.
        radians_lattitude = math.radians((a_lat + b_lat) / 2.)
        lat_lon_factor = math.cos(radians_lattitude)

        # Вычисляем смещения в метрах по вертикали и горизонтали.
        dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
        dy = abs(a_lat - b_lat) * degree_to_meters_factor

        # Вычисляем расстояние между точками.
        distance = math.sqrt(dx * dx + dy * dy)

        return distance

    def get_address(self, index, post_index_need):
        if len(self.points) == 0:
            return None
        result = ""

        address, post_index = self.points_data[index]

        result = f"Адрес: {address}"
        if post_index_need:
            result += f'\nИндекс: {post_index}'
        return result
