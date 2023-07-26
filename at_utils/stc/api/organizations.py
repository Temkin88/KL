from http import HTTPStatus
from ..decorators import for_all_methods, token_update
from at_utils import retry_wrapper


@for_all_methods(token_update)
class Organizations:
    def __init__(self, mdr_api):
        self.mdr_api = mdr_api

    @property
    def client_id(self):
        return self.mdr_api.auth.client_id

    @retry_wrapper(exception=AssertionError, n_tries=20, delay=6)
    def delete(self):
        """
        Will delete all info about client from portal if it's name match regexp
        """
        # uis_token is a Secret
        response = self.mdr_api.post(f'/{self.client_id}/organizations/delete',
                                     json={},
                                     headers={"Authorization": f"Bearer {self.mdr_api.auth.uis_token.value}"})

        assert response.status_code == HTTPStatus.OK, \
            f"Client was not deleted. SC: {response.status_code}. Msg: {response.text}"
