import config
import queue
import threading
import logging
import argparse
from daemon import Daemon

parser = argparse.ArgumentParser()
parser.add_argument("-v", default=0, action="count",
                    help="Increase verbosity.")
parser.add_argument("-V", "--version",
                    help="Show version number and exit.")
parser.add_argument("-d", choices=["start", "stop", "restart"],
                    help="Run as a daemon.")
parser.add_argument("-l", "--log",
                    help="Set log file path.")

args = parser.parse_args()

q = None
slaves = None
master = None
master_thread = None
slave_threads = None


def init():
    global q, slaves, master, master_thread, slave_threads
    # Init Queue
    q = queue.Queue()
    # Initialize Plug-ins Library
    # (Load libraries and modules and init them with Queue `q`)
    slaves = {}
    for i in config.slave_channels:
        obj = getattr(__import__(i[0], fromlist=i[1]), i[1])
        slaves[obj.channel_id] = obj(q)
    master = getattr(__import__(config.master_channel[0], fromlist=config.master_channel[1]), config.master_channel[1])(
        q, slaves)

    master_thread = threading.Thread(target=master.poll)
    slave_threads = {key: threading.Thread(target=slaves[key].poll) for key in slaves}


def poll(*args, **kwargs):
    global master_thread, slave_threads
    master_thread.start()
    for i in slave_threads:
        slave_threads[i].start()

class EFBDaemon(Daemon):
    def __init__(self, pidfile, run):
        super().__init__(pidfile)
        self.run = run

PID = "/tmp/efb.pid"
LOG = "EFB.log"

if getattr(args, "V", None):
    print("EH Forwarder Bot\n"
          "Version: Alpha 0.0 build 20161126")
else:
    if args.v == 0:
        logging.basicConfig(level=logging.ERROR)
    elif args.v == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.v >= 2:
        logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)

    if getattr(args, "log", None):
        logging.basicConfig(filename=args.log)

    if getattr(args, "d", None):
        d = EFBDaemon(PID, poll)
        logging.basicConfig(filename=LOG)
        if args.d == "start":
            init()
            d.start()
        elif args.d == "stop":
            d.stop()
        elif args.d == "restart":
            d.stop()
            init()
            d.start()
    else:
        init()
        poll()




