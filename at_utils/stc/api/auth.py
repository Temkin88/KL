import logging
import uuid
from http import HTTPStatus
from typing import List
from uuid import uuid4

import jwt
import requests
from at_utils import TEST_ENV_E2E
from at_utils.secrets import Secret

logger = logging.getLogger()


class Auth:
    def __init__(self, mdr_api=None):
        self.mdr_api = mdr_api
        self.login = None
        self.password = None
        self.client_id = None
        self.tenants = None
        self.refresh_token = None
        self.access_token = None
        self.uis_token = None
        self.session_id = None
        self.__sessions = None

    @classmethod
    def _uis_token(cls, login: str, password: (Secret, str)):
        body = {
            "grant_type": "password",
            "client_id": TEST_ENV_E2E.uis_client_id,
            "client_secret": TEST_ENV_E2E.uis_client_secret,
            "username": login,
            "password": password.value,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = f'{TEST_ENV_E2E.uis_url}/connect/token'
        response = requests.post(url, headers=headers, data=body)
        assert response.status_code == HTTPStatus.OK, f'Invalid uis access token. Status code {response.status_code}'
        return response.json()['access_token']

    def _refresh_token(self, uis_token: Secret, client_id: str, role: str = "SUPERVISOR", tenants: list = None):
        if tenants is None:
            tenants = [{"tenant_id": "-"}]
            session_name = f'autotest_tenant_{uuid4().hex}'
        else:
            session_name = f'autotest_{uuid4().hex}'

        body = {
            "session_name": session_name,
            "role": role,
            "tenants": tenants
        }
        self.mdr_api.add_headers({'Request-ID': uuid4().hex})  # add Request-ID for logs search
        self.mdr_api.set_token(uis_token.value)  # set temp uis token

        response = self.mdr_api.post(f'/{client_id}/robot_session/create', json=body)

        assert response.status_code == HTTPStatus.OK, \
            f'Invalid mdr refresh token. SC: {response.status_code}. Msg: {response.text}'

        if self.session_id:
            self.delete_session()

        response = response.json()
        refresh_token = response['refresh_token']
        self.session_id = response['session_id']
        return refresh_token

    def restart_refresh_token(self):
        response = self.mdr_api.post(f'/{self.client_id}/session/restart', json={})
        assert response.status_code == HTTPStatus.OK, \
            f'Invalid mdr refresh token. SC: {response.status_code}. Msg: {response.text}'
        self.refresh_token = response.json()['refresh_token']

    @property
    def _access_token(self):
        body = {
            "refresh_token": self.refresh_token
        }

        response = self.mdr_api.post(f'/{self.client_id}/session/confirm', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f'MDR access token was not received. SC: {response.status_code}. Msg: {response.text}'

        response = response.json()
        assert len(response) == 2, f'Response does not have enough fields. {response}'

        self.refresh_token = response['refresh_token']
        self.access_token = response['access_token']
        return self.access_token

    def to_login(self, **kwargs):
        self.login = kwargs.pop('login', TEST_ENV_E2E.mdr_login)
        self.password = Secret(kwargs.pop('password', TEST_ENV_E2E.mdr_pswd))
        self.client_id = kwargs.pop('client_id', TEST_ENV_E2E.mdr_client_id)
        self.tenants = kwargs.pop('tenants', [{"tenant_id": "-"}])
        assert not kwargs, f'Unknown parameters {kwargs}'

        self.uis_token = Secret(self._uis_token(self.login, self.password))
        self.refresh_token = self._refresh_token(self.uis_token, self.client_id, tenants=self.tenants)
        self.mdr_api.set_token(self._access_token)

    def update_access_token(self, token: str = None):
        access_token = token if token else self.access_token
        # get session_id from token
        parsed_token = jwt.decode(access_token, options={"verify_signature": False}, algorithms=["RS256"])
        previous_session_id = parsed_token['sub'].split('+')[-1]
        previous_session_id = str(uuid.UUID(previous_session_id))

        self.to_login()

        self.delete_session(previous_session_id)

    @property
    def sessions(self):
        if self.__sessions:
            return self.__sessions

        response = self.mdr_api.post(f'/{self.client_id}/robot_sessions/list', json={})
        assert response.status_code == HTTPStatus.OK, \
            f"Count has not been received. SC: {response.status_code}. Msg: {response.text}"
        self.__sessions = response.json()

        return self.__sessions

    def delete(self, session_id: str):
        body = {
            "session_id": session_id
        }
        response = self.mdr_api.post(f'/{self.client_id}/robot_sessions/delete', json=body)
        assert response.status_code == HTTPStatus.OK, \
            f"Can't delete session. SC: {response.status_code}. Msg: {response.text}"
        return response.json()

    def delete_session(self, session_id: str = None):
        session_id = session_id if session_id else self.session_id

        self.delete(session_id)
        logger.info(f'Session {session_id} was deleted')

    def delete_sessions(self, **kwargs):
        exclude: List = kwargs.pop('exclude', [])
        exclude_key: str = kwargs.pop('exclude_key', '~')

        sessions = filter(lambda x: self.session_id not in x['session_id'], self.sessions)
        sessions = filter(lambda x: not (exclude_key in x['session_name'] or x['session_name'] in exclude), sessions)
        sessions = list(sessions)

        for session in sessions:
            self.delete(session['session_id'])
            logger.info(f'Session id {session["session_id"]}: session name {session["session_name"]} was deleted')

        logger.info(f'{len(sessions)} sessions has deleted')

        self.delete_session()

    def delete_extra_sessions(self):
        """
        Do not use in automation. This method only for manual run!
        Method is deleting extra tokens except nwc tokens
        """
        self.delete_sessions(exclude_key='MDR_SESSION')
