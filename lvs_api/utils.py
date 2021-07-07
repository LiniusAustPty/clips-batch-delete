from concurrent.futures import ThreadPoolExecutor
from requests import Session as StandardSession
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession


class SessionMaker():

    @classmethod
    def make(cls, future=False, timeout=5, max_workers=10):
        if future:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            session = FuturesSession(executor=executor)
        else:
            session = StandardSession()

        adapter = TimeoutHTTPAdapter(timeout=timeout)
        session.mount(prefix="http://", adapter=adapter)
        session.mount(prefix="https://", adapter=adapter)

        return session


class TimeoutHTTPAdapter(HTTPAdapter):

    SANE_TIMEOUT = 5

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop("timeout", self.SANE_TIMEOUT)
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        kwargs["timeout"] = kwargs.pop("timeout", self.timeout)
        return super().send(request, **kwargs)


def async_callback(*args, params=None, **kwargs):
    def response_hook(response, *args, **kwargs):
        print(f"executing async callback")
        response.params = params
        response.success = False
        if response.ok:
            try:
                response.success = True
                response.data = response.json()
            except Exception as e:
                response.data = {'error': str(e)}
    return response_hook


def handle_async_responses(futures):
    results = {"success": [], "failed": []}
    for f in futures:
        response = f.result()
        if response.success:
            results["success"].append(response)
        else:
            results["failed"].append(response)
    return results
