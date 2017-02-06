from nxtools import *
from pyqtbs import *

from nx import *

DEBUG, INFO, WARNING, ERROR, GOOD_NEWS = range(5)
logging.user = "Firefly"

#
# pix library
#

def get_pix(name):
    if not name:
        return None
    if name.startswith("folder_"):
        id_folder = int(name.lstrip("folder_"))
        icn = QPixmap(12, 12)
        icn.fill(QColor(config["folders"][id_folder]["color"]))
        return icn
    pixmap = QPixmap(":/images/{}.png".format(name))
    if not pixmap.width():
        pix_file = os.path.join(app_dir, "images", "{}.png".format(name))
        if os.path.exists(pix_file):
            return QPixmap(pix_file)
    return None

class PixLib(dict):
    def __getitem__(self, key):
        if not key in self:
            self[key] = get_pix(key)
        return self.get(key, None)

pix_lib = PixLib()
