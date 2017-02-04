#!/usr/bin/env python3
import rex

from nx import *
from nx.connection import NebulaAPI

api = NebulaAPI(hub="http://dev.nebulabroadcast.com", login="demo", password="demo")

def load_settings():
    logging.info("Loading site settings")
    result = api.settings()
    if result.is_error:
        critical_error("Unable to load site settings")
    config.update(result.data)
    for config_group in [
                "storages",
                "playout_channels",
                "ingest_channels",
                "folders",
                "views"
            ]:
        ng = {}
        for id in config[config_group]:
            ng[int(id)] = config[config_group][id]
        config[config_group] = ng

load_settings()

#
#
#

result = api.rundown(id_channel=1)
if result.is_error:
    critical_error(result.message)

with open("data", "w") as f:
    f.write(json.dumps(result.data))
