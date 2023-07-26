from http import HTTPStatus

from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Incidents:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    def create(self, body: dict):
        response = self.mdr_api.post(f"/{self.client_id}/incidents/create", json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Incident has not been created. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    def count(self, body=None):
        if body is None:
            body = {}
        response = self.mdr_api.post(f"/{self.client_id}/incidents/count", json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"incident count has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def details(self, body):
        response = self.mdr_api.post(f"/{self.client_id}/incidents/details", json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Details has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def get_incidents(self, page_size: int, page_number: int, additional_body: dict = None):
        body = {
            "page_size": page_size,
            "page": page_number
        }
        if additional_body:
            body.update(additional_body)

        response = self.mdr_api.post(f'/{self.client_id}/incidents/list', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Assets list has not been received, return code {response.status_code}"
        return response.json()

    def close(self, body):
        response = self.mdr_api.post(f'/{self.client_id}/incidents/close', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Incident has not been closed. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def history(self, body):
        response = self.mdr_api.post(f'/{self.client_id}/incidents/history', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"History has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def send_email(self, body):
        response = self.mdr_api.post(f'/{self.client_id}/incidents/send/email', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Sending mail has not been received. SC: {response.status_code}. Msg: {response.text}"

    def sla_count(self, body=None):
        if body is None:
            body = {}
        response = self.mdr_api.post(f'/{self.client_id}/incidents/sla_count', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Sla count has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()
