from functools import partial

from .common import *

def create_menu(wnd):
    menubar = wnd.menuBar()

    menu_file = menubar.addMenu('&File')
    action_new_asset = QAction('&New asset', wnd)
    action_new_asset.setShortcut('Ctrl+N')
    action_new_asset.setStatusTip('Create new asset from template')
    action_new_asset.triggered.connect(wnd.new_asset)
    action_new_asset.setEnabled(has_right("asset_create"))
    menu_file.addAction(action_new_asset)

    action_clone_asset = QAction('&Clone asset', wnd)
    action_clone_asset.setShortcut('Ctrl+Shift+N')
    action_clone_asset.setStatusTip('Create new asset from current blabla')
    action_clone_asset.triggered.connect(wnd.clone_asset)
    action_clone_asset.setEnabled(has_right("asset_create"))
    menu_file.addAction(action_clone_asset)

    menu_file.addSeparator()

    action_search = QAction('Search assets', wnd)
    action_search.setShortcut('ESC')
    action_search.setStatusTip('Focus asset search bar')
    action_search.triggered.connect(wnd.search_assets)
    menu_file.addAction(action_search)

    if config["playout_channels"]:
        action_now = QAction('Now', wnd)
        action_now.setShortcut('F1')
        action_now.setStatusTip('Open current position in rundown')
        action_now.setEnabled(has_right("rundown_view"))
        action_now.triggered.connect(wnd.now)
        menu_file.addAction(action_now)

    menu_file.addSeparator()

    action_logout = QAction('L&ogout', wnd)
    action_logout.setStatusTip('Log out user')
    action_logout.triggered.connect(wnd.logout)
    menu_file.addAction(action_logout)

    action_exit = QAction('E&xit', wnd)
    action_exit.setShortcut('Alt+F4')
    action_exit.setStatusTip('Quit Firefly')
    action_exit.triggered.connect(wnd.exit)
    menu_file.addAction(action_exit)

#
# CHANNEL
#

    if config["playout_channels"]:
        wnd.menu_channel = menubar.addMenu('&Channel')
        ag = QActionGroup(wnd, exclusive=True)

        for id_channel in sorted(config["playout_channels"]):
            a = ag.addAction(
                    QAction(
                        config["playout_channels"][id_channel]["title"],
                        wnd,
                        checkable=True
                    ))
            a.id_channel = id_channel
            a.triggered.connect(partial(wnd.set_channel, id_channel))
            wnd.menu_channel.addAction(a)

#
# WINDOW
#

    menu_window = menubar.addMenu('&Window')


    action_refresh = QAction('&Refresh', wnd)
    action_refresh.setShortcut('F5')
    action_refresh.setStatusTip('Refresh views')
    action_refresh.triggered.connect(wnd.refresh)
    menu_window.addAction(action_refresh)

    menu_window.addSeparator()

    action_wnd_detail = QAction('&Object detail', wnd)
    action_wnd_detail.setShortcut('F6')
    action_wnd_detail.setStatusTip('Open detail/editor window')
    action_wnd_detail.triggered.connect(wnd.show_detail)
    menu_window.addAction(action_wnd_detail)

    action_wnd_scheduler = QAction('&Scheduler', wnd)
    action_wnd_scheduler.setShortcut('F7')
    action_wnd_scheduler.setStatusTip('Open scheduler window')
    action_wnd_scheduler.triggered.connect(wnd.show_scheduler)
    if not (has_right("scheduler_view") or has_right("scheduler_edit")):
        action_wnd_scheduler.setEnabled(False)
    menu_window.addAction(action_wnd_scheduler)

    action_wnd_rundown = QAction('&Rundown', wnd)
    action_wnd_rundown.setShortcut('F8')
    action_wnd_rundown.setStatusTip('Open rundown window')
    action_wnd_rundown.triggered.connect(wnd.show_rundown)
    if not (has_right("rundown_view") or has_right("rundown_edit")):
        action_wnd_rundown.setEnabled(False)
    menu_window.addAction(action_wnd_rundown)


#
# HELP
#

    menu_help = menubar.addMenu('Help')
    action_about = QAction('&About', wnd)
    action_about.setStatusTip('About Firefly')
    action_about.triggered.connect(partial(about_dialog, wnd))
    menu_help.addAction(action_about)
