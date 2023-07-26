from http import HTTPStatus

from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Assets:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    def count(self, body):
        if body is None:
            body = {}

        response = self.mdr_api.post(f'/{self.client_id}/assets/count', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Count has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def details(self, body):
        response = self.mdr_api.post(f'/{self.client_id}/assets/details', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Details has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def asset(self, hostname):
        if isinstance(hostname, str):
            host_names = [hostname]
        elif isinstance(hostname, list):
            host_names = hostname
        else:
            raise AssertionError(f"Unknown type hostname, expected str or list, {hostname}")
        body = {
            "host_names": host_names
        }
        response = self.mdr_api.post(f'/{self.client_id}/assets/list', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Assets list has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def all_assets(self, body: dict):
        response = self.mdr_api.post(f'/{self.client_id}/assets/list', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Assets list has not been received. SC: {response.status_code}. Msg: {response.text}"

        return response.json()

    def suggestion(self, body: dict):
        response = self.mdr_api.post(f'/{self.client_id}/assets/suggestion', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Suggestion has not been received. SC: {response.status_code}. Msg: {response.text}"

        return response.json()
