## Output - Devices connected in each FSE,WSE,Utility Pole (site type)
##

import os
import sys

import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.errors import ServerSelectionTimeoutError                                                                                                                                                             
from pymongo.errors import OperationFailure                                                                                                                                                                        
                                                                                                                                                                                                                   
from contextlib import contextmanager                                                                                                                                                                              
from configparser import ConfigParser  

from collections import defaultdict                                                                                                                                                                            
                                                                                                                                                                                                                   
CONFIG_FILE = "config.ini.example"         

def _load_config(config_file):                                                                                                                                                                                     
    """Load configs from files                                                                                                                                                                                     
    """                                                                                                                                                                                                            
    config = None
    try:
        config = ConfigParser()
        if len(config.read(config_file)) == 0:
            print("Config file [%s] is empty or not found" % config_file)
            config = None
        print("Config file loaded") 
    except:
        print("Cannot load config file [%s]" % config_file)
    return config

@contextmanager
def _connect_ossvizdb(config):
    """Connect to cpedb
    """
    db_host = config.get("ossvizdb", "host")
    db_port = config.get("ossvizdb", "port")
    db_auth = config.get("ossvizdb", "auth_db")
    db_auth_user = config.get("ossvizdb", "auth_user")
    db_auth_pwd = config.get("ossvizdb", "auth_pwd")
    db_selection_timeout = config.get("ossvizdb", "selection_timeout")
    db_socket_timeout = config.get("ossvizdb", "socket_timeout")
    db_connect_timeout = config.get("ossvizdb", "connect_timeout")
    #dbclient = pymongo.MongoClient("mongodb://{0}:{1}/{2}?serverSelectionTimeoutMS={3}&socketTimeoutMS={4}&connectTimeoutMS={5}".format(
                                    #db_host,db_port,db_auth,db_selection_timeout,db_socket_timeout,db_connect_timeout))
    dbclient = pymongo.MongoClient("mongodb://{0}:{1}@{2}:{3}/{4}?serverSelectionTimeoutMS={5}&socketTimeoutMS={6}&connectTimeoutMS={7}".format(
                                    db_auth_user, db_auth_pwd, db_host, db_port, db_auth, db_selection_timeout, db_socket_timeout, db_connect_timeout))
    try:
        dbclient.admin.command("ismaster")
        print("Mongo: DB Connected")
    except ServerSelectionTimeoutError:
        print("Mongo: Database connection failed. ServerSelectionTimedOut")
        dbclient = None
    except ConnectionFailure:
        print("Mongo: Database connection failed. Connection Failure")
        dbclient = None
    except OperationFailure:
        print("Mongo: Database connection failed. Authentication Failed")
        dbclient = None
    except:
        print(traceback.format_exc())
    yield dbclient
    _close_db(dbclient)
    print("MongoDB : DB connection closed")

def _close_db(db):
    if db is not None:
        try:
            db.close()
        except:
            pass
    return

def _get_devices_records(_device,_device_type,_dev_id):
	rec = _device.find({"_id": _dev_id})
	for dev_rec in rec:
		type_id = dev_rec.get('device_type_id')
		type_macs = dev_rec.get('mac')
		return type_macs

def _get_devices_list(records,ossviz):
	_site = ossviz.site
	_inst_device = ossviz.installed_devices
	_device = ossviz.device
	_device_type = ossviz.device_type
	for item in records:
		_id = item.get('_id')

		site_records = _site.find({"site_type_id": _id})
		for site in site_records:
			current_devices = dict()
			res = dict()
			_sid = site.get('_id')
			_ref = site.get('ref_code')
			_devices_list = list()

			installed_records = _inst_device.find({"site_id": _sid})
			for dev in installed_records:

				_dev_id = dev.get('device_id')

				_devices_records = _get_devices_records(_device,_device_type,_dev_id)
				_devices_list.append(_devices_records)

			current_devices['pole_id'] = _ref
			current_devices['devices'] = list()
			current_devices['devices'] = _devices_list
			print(current_devices)

			# res[_ref] = _devices_list
			# return res

def main():
	config = _load_config(CONFIG_FILE)
	if config is None:
		sys.exit(0)
	with _connect_ossvizdb(config) as mongodb_client:
		if not mongodb_client:
			return
		ossviz = mongodb_client.ossvizdb
		_site_type = ossviz.site_type

		pole_type = ['FSE','WSE','Utility Pole']
		pole_list = list()
		for pole in pole_type:
			type_records = _site_type.find({"name": pole})
			_device = _get_devices_list(type_records,ossviz)
			
					

if __name__ == "__main__":
	main()
	sys.exit(0)