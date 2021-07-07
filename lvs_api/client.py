import logging
from urllib.parse import urlencode
import requests
from utils import SessionMaker
from utils import async_callback, handle_async_responses

logger = logging.getLogger(__name__)


class LvsApiSession:

    base_url = "https://api.lvs.linius.com"
    http_methods = ['GET', 'PUT', 'POST', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']

    def __init__(self, api_key, username, password):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.future_session = SessionMaker.make(future=True, timeout=30)
        self.standard_session = SessionMaker.make(future=False, timeout=30)
        self.token = self.get_token()
        self.unauthorized = False

    @property
    def headers(self):
        return {
            'X-Api-Key': self.api_key,
            'Authorization': f"Bearer {self.token}",
            'Content-Type': 'application/json',
        }

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            if name.upper() in self.http_methods:
                return self._request(name, *args, **kwargs)
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
        return _missing

    def _request(self, verb, endpoint, json=None, future=False, headers=None, **opts):
        if future:
            self.token = self.get_token()
            session = self.future_session
        else:
            session = self.standard_session

        headers = headers or {}
        response =  getattr(session, verb)(
            f"{self.base_url}{endpoint}",
            headers={**self.headers, **headers},
            json=json,
            **opts
        )

        if not future and response.status_code == 401:
            self.token = self.get_token()
            return self._request(verb, endpoint, json, future, **opts)

        return response

    def get_token(self):
        data = {'userName': self.username, 'password': self.password}
        response = requests.post(f"{self.base_url}/v2/iam/auth/signin", json=data)
        response.raise_for_status()
        return response.json()['token']


class LvsApiClient:

    def __init__(self, api_key, username, password):
        self.session = LvsApiSession(api_key, username, password)

    def async_delete_clips(self, clips):
        print("executing async delete clips")
        futures = [
            self.session.delete(
                f"/v3/search/{c['id']}",
                hooks={"response": async_callback(params={"clip": c})},
                future=True
            )
            for c in clips
        ]
        return handle_async_responses(futures)

    def purge_all_asset_clips(self, asset_id):
        asset = self.get_asset_with_clips(asset_id)
        return self.async_delete_clips(asset['clips'])

    def get_asset(self, asset_id):
        response = self.session.get(f"/v3/asset/{asset_id}")
        response.raise_for_status()
        return response.json()

    def get_asset_with_clips(self, asset_id):
        asset = self.get_asset(asset_id)
        asset['clips'] = self.get_asset_clips(asset_id)
        return asset

    def get_asset_clips(self, asset_id, limit=100):
        query_clauses = [
            "payload.category:ASSET_TAG",
            "payload.category:ASSET_START_DATE",
            "payload.category:ASSET_END_DATE"
        ]
        query = f"assetId:{asset_id} AND NOT ({(' OR ').join(query_clauses)})"
        params = {'sortDesc': 'false', 'sortMode': 'startTime', 'pageSize': limit}

        clips = []
        total_clips = 0
        page_index = 0
        last_page = False
        first_page = True
        while first_page or not last_page:
            def make_request(index):
                params['page'] = index
                url = f"/v3/search?query={query}&{urlencode(params)}"
                return self.session.get(url)

            response = make_request(page_index)

            response.raise_for_status()
            data = response.json()
            clips += data['content']
            last_page = data.get('last', True)
            total_pages = data.get('totalPages')
            total_clips = data.get('totalElements')
            print(f"[{asset_id}] - pages: {total_pages} page_index: {page_index}, clips: {len(clips)}")

            page_index += 1
            first_page = False

        if len(clips) != total_clips:
            raise Exception(f"clips missing for asset_id: {asset_id}")

        print(f"fetched clips total: {total_clips}, asset_id {asset_id}")
        return clips
