import functools

from firefly import *
from firefly.dialogs.rundown import *

DEFAULT_COLUMNS = [
        "rundown_symbol",
        "title",
        "identifier/main",
        "duration",
        "run_mode",
        "rundown_scheduled",
        "rundown_broadcast",
        "rundown_difference",
        "rundown_status",
        "mark_in",
        "mark_out",
        "id_asset",
        "id_object"
    ]


class RundownModel(FireflyViewModel):
    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def start_time(self):
        return self.parent().start_time

    def load(self, **kwargs):
        load_start_time = time.time()
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        logging.info("Loading rundown. Please wait...")

        result = api.rundown(id_channel=self.id_channel, start_time=self.start_time)
        if result.is_error:
            QApplication.restoreOverrideCursor()
            return

        reset = True
        required_assets = []
        self.beginResetModel()

        self.header_data = DEFAULT_COLUMNS
        self.object_data = []

        for row in result.data:
            if row["object_type"] == "event":
                self.object_data.append(Event(meta=row))
            elif row["object_type"] == "item":
                required_assets.append([row["id_asset"], row["asset_mtime"]])
                self.object_data.append(Item(meta=row))
            else:
                continue

        asset_cache.request(required_assets)

        if reset:
            self.endResetModel()
        elif changed_rows:
            self.dataChanged.emit(
                    self.index(min(changed_rows), 0),
                    self.index(max(changed_rows), len(self.header_data)-1)
                )

        QApplication.restoreOverrideCursor()
        logging.goodnews(
                "{} rows of {} rundown loaded in {:.03f}".format(
                    len(result.data),
                    format_time(self.start_time, "%Y-%m-%d"),
                    time.time() - load_start_time
                )
            )



    def refresh_assets(self, assets):
        for row in range(len(self.object_data)):
            if self.object_data[row].object_type == "item" and self.object_data[row]["id_asset"] in assets:
                self.object_data[row]._asset = asset_cache[self.object_data[row]["id_asset"]]
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.header_data)-1))

    def refresh_items(self, items):
        for row, obj in enumerate(self.object_data):
            if self.object_data[row].id in items and self.object_data[row].object_type == "item":
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.header_data)-1))
                break


    def flags(self,index):
        flags = super(RundownModel, self).flags(index)
        if index.isValid():
            obj = self.object_data[index.row()]
            if obj.id and obj.object_type == "item":
                flags |= Qt.ItemIsDragEnabled # Itemy se daji dragovat
        else:
            flags = Qt.ItemIsDropEnabled # Dropovat se da jen mezi rowy
        return flags

    def mimeTypes(self):
        return ["application/nx.asset", "application/nx.item"]

    def mimeData(self, indexes):
        mimeData = QMimeData()

        data = [self.object_data[i] for i in set(index.row() for index in indexes if index.isValid())]
        encodedIData = json.dumps([i.meta for i in data])
        mimeData.setData("application/nx.item", encodedIData)

        encodedAData = json.dumps([i.asset.meta for i in data])
        mimeData.setData("application/nx.asset", encodedAData)
        try:
            urls = [QUrl.fromLocalFile(item.asset.file_path) for item in data]
            mimeData.setUrls(urls)
        except:
            pass
        return mimeData


    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if not user.has_right("rundown_edit", self.id_channel):
            logging.warning("You are not allowed to modify this rundown")
            return True

        if row < 1:
            return False

        drop_objects = []
        if data.hasFormat("application/nx.item"):
            iformat = ITEM
            d = data.data("application/nx.item").data()
            items = json.loads(d.decode("ascii"))
            if not items or items[0].get("rundown_row","") in [row, row-1]:
                return False
            else:
                for obj in items:
                    if not obj.get("id_object", False) and obj.get("item_role", False) in ITEM_ROLES:
                        dlg = PlaceholderDialog(self.parent(), obj["item_role"])
                        dlg.exec_()
                        if not dlg.ok:
                            return
                        for key in dlg.meta:
                            obj[key] = dlg.meta[key]

                    drop_objects.append(Item(from_data=obj))

        elif data.hasFormat("application/nx.asset"):
            iformat = ASSET
            d = data.data("application/nx.asset").data()
            items = json.loads(d.decode("ascii"))
            for obj in items:
                drop_objects.append(Asset(from_data=obj))
        else:
            return False



        pre_items = []
        dbg = []
        i = row-1
        to_bin = self.object_data[i]["rundown_bin"]

        while i >= 1:
            if self.object_data[i].object_type != "item" or self.object_data[i]["rundown_bin"] != to_bin: break
            p_item = self.object_data[i].id

            if not p_item in [item.id for item in drop_objects]:
                pre_items.append({"object_type" : ITEM, "id_object" : p_item, "params" : {}})
                dbg.append(self.object_data[i].id)
            i-=1
        pre_items.reverse()


        for obj in drop_objects:
            if data.hasFormat("application/nx.item"):
                pre_items.append({"object_type" : ITEM, "id_object" : obj.id, "params" : obj.meta})
                dbg.append(obj.id)

            elif data.hasFormat("application/nx.asset"):
                mark_in = mark_out = False

                params = {}

                if obj["subclips"]:
                    dlg = SubclipSelectDialog(self.parent(), obj)
                    dlg.exec_()
                    if dlg.ok:
                        mark_in, mark_out = dlg.marks
                        if dlg.clip:
                            params["title"] = "{} ({})".format(obj["title"], dlg.clip)
                else:
                    mark_in  = obj["mark_in"]
                    mark_out = obj["mark_out"]

                if mark_in:  params["mark_in"]  = mark_in
                if mark_out: params["mark_out"] = mark_out
                pre_items.append({"object_type" : ASSET, "id_object" : obj.id, "params" : params})

        i = row
        while i < len(self.object_data):
            if self.object_data[i].object_type != "item" or self.object_data[i]["rundown_bin"] != to_bin: break
            p_item = self.object_data[i].id

            if not p_item in [item.id for item in drop_objects]:
                pre_items.append({"object_type" : ITEM, "id_object" : p_item, "params" : {}})
                dbg.append(self.object_data[i].id)
            i+=1

        if pre_items:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            stat, res = query("bin_order", id_bin=to_bin, order=pre_items, sender=self.parent().parent().objectName())
            QApplication.restoreOverrideCursor()
            if success(stat):
                logging.info("Bin order changed")
            else:
                logging.warning( "Error {} : {}".format(stat, res))
            self.load()
        return True

