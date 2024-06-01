import asyncio, logging, aiofiles
from asyncio.locks import Lock
from json import loads
from pathlib import PurePath

class IpAuth:
     
    UNIVERSAL_IP = "0.0.0.0"

    def __init__(self):

        logging.info("starting Ip auth script...")
        self.settings_path = PurePath(__file__).parent / "ipauth_settings.json"
        
        self.server_host_lock = Lock()
        self.server_host = ""
        self.server_port_lock = Lock()
        self.server_port = 0
        self.ws_host_lock = Lock()
        self.ws_host = ""
        self.ws_port_lock = Lock()
        self.ws_port = 0
        self.valid_ips_lock = Lock()
        self.valid_ips = []

        asyncio.create_task(self.monitor_settings())

    def requestheaders(self, flow):
        ## check if proxy authentication headers contain valid userid and authcode
        valid = False 
        if flow.client_conn.peername[0] in self.valid_ips or IpAuth.UNIVERSAL_IP in self.valid_ips:

            valid = True

        if not valid:

            flow.kill() ## if credentials are not valid, kill flow

        if "https" in flow.request.scheme:

            flow.request.scheme = "http"

        elif "wss" in flow.request.scheme:

            flow.request.scheme = "ws"

        if "http" in flow.request.scheme:

            flow.request.host = self.server_host
            flow.request.port = self.server_port

        elif "ws" in flow.request.scheme:

            flow.request.host = self.ws_host
            flow.request.port = self.ws_port

    async def monitor_settings(self):

        self.settings = await aiofiles.open(self.settings_path, 'r') ## settings json file should be structures like
        """{
                "server_host" : "",
                "server_port" : 0,
                "valid_ips" : []
            }
        """
        logging.info("starting ip maintance cycle...")
        count = 0 ## to enable retry up to 5 counts
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

                await self.ws_host_lock.acquire()
                self.ws_host = settings_data["ws_host"]
                self.ws_host_lock.release()

                await self.ws_port_lock.acquire()
                self.ws_port = settings_data["ws_port"]
                self.ws_port_lock.release()

                ## update ip lists
                await self.valid_ips_lock.acquire()
                self.valid_ips = settings_data["valid_ips"]
                self.valid_ips_lock.release()

            logging.debug("completed maintance cycle")
            await asyncio.sleep(60 * 1) ## sleep for 5 minutes

    def __del__(self):
        
        logging.info("stopping Ip auth script...")
        #asyncio.run(self.settings.close())

addons = [IpAuth()]
