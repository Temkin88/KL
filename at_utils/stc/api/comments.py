from http import HTTPStatus

from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Comments:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    def create(self, body):
        response = self.mdr_api.post(f"/{self.client_id}/comments/create", json=body)
        assert response.status_code == HTTPStatus.OK,\
            f"Failed to create comment. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def delete(self, body: dict):
        response = self.mdr_api.post(f"/{self.client_id}/comments/delete", json=body)
        assert response.status_code == HTTPStatus.OK,\
            f"Failed to delete comment. SC: {response.status_code}. Msg: {response.text}"
