
import threading
from bots import waitdragon
from bots import pricepixie
from bots import weatherwatcher

def launch_system():
    threading.Thread(target=waitdragon.run).start()
    threading.Thread(target=pricepixie.run).start()
    threading.Thread(target=weatherwatcher.run).start()

if __name__ == "__main__":
    launch_system()
