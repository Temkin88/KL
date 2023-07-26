from http import HTTPStatus

from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Schedules:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    def delete(self):
        # uis_token is a Secret
        response = self.mdr_api.post(f'/{self.client_id}/schedules/delete',
                                     json={'type': 'weekly'},
                                     headers={"Authorization": f"Bearer {self.mdr_api.auth.uis_token.value}"})
        assert response.status_code == HTTPStatus.OK, \
            f"Schedule has not been deleted. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def create(self, body):
        # uis_token is a Secret
        response = self.mdr_api.post(f'/{self.client_id}/schedules/create',
                                     json=body,
                                     headers={"Authorization": f"Bearer {self.mdr_api.auth.uis_token.value}"})

        assert response.status_code == HTTPStatus.OK, \
            f"Schedule has not been created. SC: {response.status_code}. Msg: {response.text}"

        return response.json()

    def get(self):
        # uis_token is a Secret
        response = self.mdr_api.post(f'/{self.client_id}/schedules/list',
                                     json={},
                                     headers={"Authorization": f"Bearer {self.mdr_api.auth.uis_token.value}"})

        assert response.status_code == HTTPStatus.OK, \
            f"Schedule list has not been received. SC: {response.status_code}. Msg: {response.text}"

        return response.json()
