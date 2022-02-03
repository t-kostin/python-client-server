import sys
import os
import argparse
import configparser
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from modules.arg_types import ip_address, port
from loggers.server_log_config import SERVER_LOG
from modules.messenger import JimServer
from modules.server_db import ServerDB
import modules.arg_types
from modules.gui_server import MainWindow, gui_create_model,\
    HistoryWindow, create_stat_model, ConfigWindow
from modules.user_management import AddUser, DeleteUser


def server_run(server):
    server.listen()


def main():
    SERVER_LOG.debug('Application is started')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a',
        type=ip_address,
        default='',
        dest='ip_addr',
        help='valid server IP address: ddd.ddd.ddd.ddd or localhost',
    )
    parser.add_argument(
        '-p',
        type=port,
        default=7777,
        dest='port',
        help='server port: integer from 1024 to 65535',
    )
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config_file_with_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'server.ini',
    )
    config.read(config_file_with_path)

    db_file_name = os.path.join(
        config['SETTINGS']['database_path'],
        config['SETTINGS']['database_file'],
    )
    def_ip_addr = args.ip_addr if args.ip_addr != '' \
        else config['SETTINGS']['listen_address']
    def_port = args.port if args.port != 7777 \
        else int(config['SETTINGS']['default_port'])

    server_db = ServerDB(db_file_name)
    my_server = JimServer(def_ip_addr, def_port, server_db, SERVER_LOG)
    server_thread = threading.Thread(
        target=server_run,
        args=(my_server,),
        daemon=True,
    )
    server_thread.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(server_db))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        if my_server.clients_number_changed:
            main_window.active_clients_table.setModel(
                gui_create_model(server_db))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            my_server.clients_refreshed()

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(server_db))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            new_port = modules.arg_types.port(config_window.port.text())
            new_ip = modules.arg_types.ip_address(config_window.ip.text())
        except ValueError:
            message.warning(
                config_window,
                'Error',
                'Port or IP address are invalid')
        else:
            config['SETTINGS']['Default_port'] = str(new_port)
            config['SETTINGS']['Listen_Address'] = new_ip
            with open(config_file_with_path, 'w') as conf:
                config.write(conf)
                message.information(
                    config_window,
                    'OK',
                    'Configuration successfully saved'
                )

    def add_user():
        global add_user_window
        add_user_window = AddUser(server_db, my_server)
        # add_user_window.show()

    def del_user():
        global del_user_window
        del_user_window = DeleteUser(server_db, my_server)
        # del_user_window.show()

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
    main_window.add_btn.triggered.connect(add_user)
    main_window.del_btn.triggered.connect(del_user)

    server_app.exec_()

    my_server.shutdown()
    server_thread.join()


if __name__ == '__main__':
    main()
