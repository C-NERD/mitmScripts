import asyncio, logging, aiofiles
from asyncio.locks import Lock
from json import loads
from pathlib import PurePath

class ReverseProxy:

    def __init__(self):

        logging.info("starting Reverse proxy script...")
        self.settings_path = PurePath(__file__).parent / "reverseproxy_settings.json"
        
        self.server_host_lock = Lock()
        self.server_host = ""
        self.server_port_lock = Lock()
        self.server_port = 0 

        asyncio.create_task(self.monitor_settings())

    def requestheaders(self, flow):

        flow.request.host = self.server_host
        flow.request.port = self.server_port

        ## This is because I do not expect server behind reverseproxy to be using ssl
        if "https" in flow.request.scheme:

            flow.request.scheme = "http"

        elif "wss" in flow.request.scheme:

            flow.request.scheme = "ws"

    async def monitor_settings(self):

        self.settings = await aiofiles.open(self.settings_path, 'r') ## settings json file should be structures like
        """{
                "server_host" : "",
                "server_port" : 0,
            }
        """
        logging.info("starting proxy maintance cycle...")
        count = 0 ## to enable retry up to 5 counts
        settings_data = {}
        while True:
            
            logging.info("new maintance cycle")
            updated = False
            try:

                ## check for settings update
                await self.settings.seek(0)
                settings_data = loads(await self.settings.read())
                updated = True

            except:
                
                if count < 5:

                    count += 1
                    continue

                else:

                    count = 0
            
            if updated:

                ## update server_url
                await self.server_host_lock.acquire()
                self.server_host = settings_data["server_host"]
                self.server_host_lock.release()

                await self.server_port_lock.acquire()
                self.server_port = settings_data["server_port"]
                self.server_port_lock.release()

            logging.debug("completed maintance cycle")
            await asyncio.sleep(60 * 1) ## sleep for 5 minutes

    def __del__(self):
        
        logging.info("stopping Ip auth script...")
        #asyncio.run(self.settings.close())

addons = [ReverseProxy()]
