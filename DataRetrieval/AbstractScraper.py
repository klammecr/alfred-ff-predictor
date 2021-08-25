import requests

class AbstractScraper(object):
    """
    Set up everything for multiprocessing/a standalone server process
    The only thing that should be the same between everything is the:
        1. User session
        2. Proxy IP
        3. Port
    """
    def __init__(self, reqDelay):
        self.m_req_delay = reqDelay
        self.m_ssn = requests.Session()

        # Headers to emulate an default user session
        self.m_ssn.headers.update({
         'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
         'accept': 'text/html',
         'accept-language': 'en-US,en;q=0.9'
        })

        """
        No need right now, if we need it, we can put it in
        # Set the proxy server
        proxies = {
          "http": "http://" + self.m_proxy["ip"] + ":" + self.m_proxy["port"],
          "https": "https://" + self.m_proxy["ip"] + ":" + self.m_proxy["port"]
        }
        self.m_ssn.proxies.update(proxies)
        """