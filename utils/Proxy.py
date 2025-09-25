from swiftshadow.classes import ProxyInterface

class Proxy:
    def __init__(self):
        self.proxy_manager = ProxyInterface(
                            protocol="http",
                            autoRotate=True
                        )

    def get_proxy(self):
        proxy = self.proxy_manager.get().as_string()
        return proxy
    

if __name__ == "__main__":
    print(Proxy().get_proxy())
