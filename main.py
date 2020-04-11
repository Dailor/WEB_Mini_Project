import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QLineEdit, QLabel, QPushButton, QRadioButton, QVBoxLayout, \
    QPlainTextEdit, QComboBox
from PyQt5.Qt import QPixmap, QKeyEvent, Qt, QMouseEvent, QPoint
from PyQt5 import uic

from modules import CONST
from modules.map import Map as MapInteractive


def updateMapPicture(func):
    def wrapper(self, *args, **kwargs):
        if func(self, *args, **kwargs) is not False:
            self.update_map()

    return wrapper


class MapApplication(QMainWindow):
    def __init__(self):
        super().__init__()

        if False:
            self.searchEdit = QLineEdit()
            self.findButton = QPushButton()
            self.mapLabel = QLabel()
            self.map_type_layout = QVBoxLayout()
            self.resetFindButton = QPushButton()
            self.full_address_edit = QPlainTextEdit()
            self.point_comboBox = QComboBox()
            self.index_off_radioButton = QRadioButton()
            self.index_on_radioButton = QRadioButton()

        self.map = MapInteractive()
        self.post_code = True

        self.load_ui()

    def load_ui(self):
        uic.loadUi(CONST.MAIN_UI_PATH, self)
        first_checked = False
        for title, keep in CONST.MAP_TYPES:
            btn = QRadioButton()
            btn.map_type = keep
            btn.setText(title)
            btn.setFont(CONST.MAP_TYPE_FONT)
            btn.clicked.connect(self.map_type_change)
            btn.in_layout = self.map_type_layout

            if first_checked is False:
                first_checked = True
                btn.setChecked(True)

            self.map_type_layout.addWidget(btn)

        self.index_on_radioButton.setChecked(True)

        self.findButton.clicked.connect(self.find_obj)
        self.resetFindButton.clicked.connect(self.reset_all_found)

        self.index_off_radioButton.clicked.connect(self.change_post_code)
        self.index_on_radioButton.clicked.connect(self.change_post_code)

        self.point_comboBox.currentIndexChanged.connect(self.change_address_text)

        self.update_map()

    def change_address_text(self, index):
        if index == -1:
            return
        self.full_address_edit.setPlainText(self.map.get_address(index, self.post_code))

    def update_map(self):
        map_bytes = self.map.get_map_bytes()
        qpix = QPixmap()
        qpix.loadFromData(map_bytes)
        self.mapLabel.setPixmap(qpix)

    def change_post_code(self, checked):
        btn = self.sender()
        if btn == self.index_off_radioButton:
            self.post_code = False
        else:
            self.post_code = True
        self.change_address_text(self.point_comboBox.currentIndex())

    @updateMapPicture
    def find_obj(self, pressed):
        text = self.searchEdit.text()
        if len(text) == 0:
            return False
        data = self.map.get_obj_data(text)
        if data is None:
            return False

        obj = data[0]
        pos = obj["pos"]
        addr = obj["address"]
        post_code = obj["post_code"]

        self.map.set_center(pos)
        self.add_points_data(pos, addr, post_code)

        self.searchEdit.clear()

    def add_points_data(self, pos, addr, post_code):
        self.map.add_point(pos, addr, post_code)
        self.point_comboBox.addItem(str(self.map.get_points_count()))
        self.point_comboBox.setCurrentIndex(self.map.get_points_count() - 1)

    @updateMapPicture
    def reset_all_found(self, pressed):
        self.point_comboBox.clear()
        self.full_address_edit.clear()
        return self.map.clear_points()

    @updateMapPicture
    def map_type_change(self, checked):
        btn = self.sender()
        if False:
            btn = QRadioButton()
        btn.clearFocus()
        if btn.in_layout == self.map_type_layout:
            self.map.setMapType(btn.map_type)

    @updateMapPicture
    def keyPressEvent(self, keyPressed: QKeyEvent, *args, **kwargs):
        key = keyPressed.key()
        if key == Qt.Key_Escape:
            self.searchEdit.clearFocus()
            return False
        elif key == Qt.Key_Up:
            self.map.move_on_map(CONST.MOVE_UP)
        elif key == Qt.Key_Down:
            self.map.move_on_map(CONST.MOVE_DOWN)
        elif key == Qt.Key_Left:
            self.map.move_on_map(CONST.MOVE_LEFT)
        elif key == Qt.Key_Right:
            self.map.move_on_map(CONST.MOVE_RIGHT)
        elif key == Qt.Key_PageUp:
            self.map.setScale(CONST.UP_SCALE)
        elif key == Qt.Key_PageDown:
            self.map.setScale(CONST.DOWN_SCALE)
        else:
            return False

    @updateMapPicture
    def obj_by_click(self, pos_click, close_to_click=None):
        longitude, latitude = self.get_lonlat_from_pix(pos_click)

        if self.map.check_coord((longitude, latitude)) is False:
            return False

        if close_to_click is not None:
            close_to_click = longitude, latitude

        obj = self.map.get_obj_data(f"{latitude},{longitude}", close_to_click=close_to_click)

        if obj is None:
            return False

        obj = obj[0]
        pos = obj["pos"]
        addr = obj["address"]
        post_code = obj["post_code"]

        if close_to_click is None:
            self.add_points_data((longitude, latitude), addr, post_code)
        else:
            self.add_points_data(pos, addr, post_code)

    def find_close_org(self, pos_click):
        longitude, latitude = self.get_lonlat_from_pix(pos_click)

        if self.map.check_coord((longitude, latitude)) is False:
            return False

    def mousePressEvent(self, event: QMouseEvent):
        # key == 1 left; key == 2 right

        pos_rel_app = event.pos()
        key = event.button()

        pos_rel_map = pos_rel_app.x() - self.mapLabel.x(), pos_rel_app.y() - self.mapLabel.y()
        if 0 < pos_rel_map[0] < self.mapLabel.width() and 0 < pos_rel_map[1] < self.mapLabel.height():
            if key == 1:
                self.obj_by_click(pos_rel_map)
            elif key == 2:
                self.obj_by_click(pos_rel_map, True)

    def get_lonlat_from_pix(self, click_pos):
        map_pos = self.map.position

        dx_degrees = (click_pos[0] - self.mapLabel.width() // 2) * self.map.get_delta_longitude_per_scale / 2
        dy_degrees = (click_pos[1] - self.mapLabel.height() // 2) * self.map.get_delta_latitude_per_scale / 4

        longitude = map_pos[0] + dx_degrees
        latitude = map_pos[1] - dy_degrees
        return longitude, latitude


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MapApplication()
    ex.show()
    sys.exit(app.exec_())
