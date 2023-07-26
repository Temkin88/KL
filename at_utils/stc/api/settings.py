from http import HTTPStatus

from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Settings:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    @property
    def auto_accept(self):
        response = self.mdr_api.post(f'/{self.client_id}/settings/auto_response/get', json={})
        assert response.status_code == HTTPStatus.OK, f"Auto accepting response has not been set. " \
                                                      f"Status code {response.status_code}"
        return response.json()['auto_response']

    @auto_accept.setter
    def auto_accept(self, state: bool):
        body = {
            'auto_response': state
        }

        response = self.mdr_api.post(f'/{self.client_id}/settings/auto_response/set', json=body)
        assert response.status_code == HTTPStatus.OK, f"Auto accepting response status has not been received. " \
                                                      f"Status code {response.status_code}"
