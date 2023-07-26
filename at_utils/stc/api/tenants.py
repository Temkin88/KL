from http import HTTPStatus
from ..decorators import for_all_methods, token_update


@for_all_methods(token_update)
class Tenants:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    def create(self, body: dict):
        response = self.mdr_api.post(f'/{self.client_id}/tenants/create', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Tenant {body} has not created. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def delete(self, body: dict):
        """
        Need to login as tenant to use this method mdr_manager.login(tenants=[{"tenant_id": tenant_id}])
        """
        response = self.mdr_api.post(f'/{self.client_id}/tenants/delete', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Tenant {body} has not deleted. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    @property
    def tenants(self):
        headers = {"Authorization": f"Bearer {self.mdr_api.auth.uis_token.value}"}
        response = self.mdr_api.post(f'/{self.client_id}/tenants/list', json={}, headers=headers)

        assert response.status_code == HTTPStatus.OK, \
            f"Tenant list has not been received. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def tenant_info(self, tenant_name: str):
        for tenant in self.tenants:
            if tenant_name == tenant['tenant_name']:
                return tenant

        raise AssertionError(f'Tenant with name {tenant_name} has not been found in {self.tenants}')
