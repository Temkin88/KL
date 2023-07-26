import logging
import random
from typing import Optional, List

import TEST_ENV_E2E
import MDRRestAPi

logger = logging.getLogger()


class MDRManager:
    """
    This class wrapper for work with MDRRestApi
    """

    def __init__(self, url: str = None, client_id: str = None):
        """
        param: client_id: userDescriptionEx
        """
        self.url = url or TEST_ENV_E2E.mdr_url
        self.client_id = client_id or TEST_ENV_E2E.mdr_client_id
        self.api = MDRRestAPi(address=self.url, prefix="api/v1")
        self.login(client_id=self.client_id)

    def __getattr__(self, attr):
        return getattr(self.api, attr)

    """
    -------------GENERAL API-------------
    """

    def login(self, **kwargs):
        delete_session = kwargs.pop("delete_session", True)

        self.client_id = kwargs.get("client_id") or self.client_id
        kwargs["client_id"] = self.client_id

        if self.auth.session_id and delete_session:
            self.auth.delete_session(self.auth.session_id)

        self.auth.to_login(**kwargs)

    def delete_tenant(self, tenant_id: str) -> None:
        """
        Access token with root tenant does not have access to tenant.
        Need access token with access to tenant for delete
        """
        tenant = {"tenant_id": tenant_id}
        self.auth.to_login(tenants=[tenant])
        self.tenants.delete(tenant)
        self.auth.update_access_token()

    """
    -------------SCHEDULES API-------------
    """

    def delete_schedules(self):
        """
        Delete schedule if it is exist
        """
        if "weekly" in [_id["type"] for _id in self.schedules.get()]:
            self.schedules.delete()

    """
    -------------ASSETS API-------------
    """
    @property
    def get_all_assets(self):
        page_size = 10000
        offset = 1
        page = True
        result = []

        while page:
            body = {
                "page_size": page_size,
                "page": offset
            }
            response = self.api.assets.all_assets(body)

            offset += 1
            page = response
            result.extend(page)

        return result

    def machine_sid3(self, host_name: str):
        for asset in self.get_all_assets:
            if host_name == asset.get('hostName'):
                return asset['assetId']

        raise ValueError(f"This host name {host_name} was not found")

    @property
    def random_machine(self):
        asset = random.choice(self.get_all_assets)
        return asset["host_name"], asset["asset_id"]

    def get_assets_by_hostname(self, asset_name):
        assets = [asset for asset in self.get_all_assets if asset_name.upper() in asset["host_name"]]
        return assets

    def asset_machinesid3(self, asset_name: str):
        assets_by_hostname = self.get_assets_by_hostname(asset_name)
        assets_by_hostname.sort(key=lambda asset: asset["last_seen"])
        last_asset = assets_by_hostname.pop()
        return last_asset["asset_id"]

    def assets_by_last_seen(self, platform, product):
        assets_by_hostname = [asset for asset in self.get_all_assets
                              if platform in asset["os_version"] and product in asset["product_map"]]
        assets_by_hostname.sort(key=lambda asset: asset["last_seen"])
        return assets_by_hostname

    def assets_by_statuses(self, status):
        assets = [asset["host_name"] for asset in self.assets.get_all_assets if status in asset["status"]]
        return assets

    def get_assets_count(self, body=None):
        count = self.api.assets.count(body)
        return count["count"]

    def get_assets_details(self, assets_id, fields: list = None):
        body = {
            "asset_id": assets_id
        }
        if fields:
            body["fields"] = fields

        return self.api.assets.details(body)

    def get_assets_suggestion(self, search_phrase, tenants_names: list = None):
        body = {
            "search_phrase": search_phrase
        }
        if tenants_names:
            body["tenants_names"] = tenants_names
        return self.api.assets.suggestion(body)

    """
    -------------ORGANIZATIONS API-------------
    """
    def delete_organizations(self):
        self.api.organizations.delete()

    """
    -------------INCIDENTS API-------------
    """
    def get_list_incidents(self, page_size=100, max_page=100, additional_body=None):
        page_size = page_size
        offset = 1
        result = []

        while offset <= max_page:
            response = self.api.incidents.get_incidents(page_size, offset, additional_body)

            offset += 1
            result.extend(response)

        return result

    @property
    def get_all_incidents(self):
        return self.get_list_incidents()

    def create_incident(self, affected_hosts: List[str], client_description, summary,
                        priority="HIGH", tenant_id="", no_sla_flag=False):
        body = {
            "affected_hosts": affected_hosts,
            "client_description": client_description,
            "priority": priority,
            "summary": summary,
            "tenant_id": tenant_id,
            "no_sla_flag": no_sla_flag
        }
        return self.api.incidents.create(body)

    def get_incident_count(self, body=None):
        count = self.api.incidents.count(body)
        return count["count"]

    def close_incident(self, incident_id, summary="Test", resolution_status="FALSE_POSITIVE"):
        body = {
            "incident_id": incident_id,
            "summary": summary,
            "resolution_status": resolution_status
        }
        return self.api.incidents.close(body)

    def get_incident_details(self, incident_id: str, fields: list = None):
        body = {
            "incident_id": incident_id
        }
        if fields:
            body["fields"] = fields

        return self.api.incidents.details(body)

    def incident_send_email(self, issue_key: str, issue_type: str, user_email: str):
        body = {
          "issue_key": issue_key,
          "issue_type": issue_type,
          "user_email": user_email
        }
        return self.api.incidents.send_email(body)

    def get_incident_sla_count(self, body=None):
        return self.api.incidents.sla_count(body)

    def get_incidents_history(
        self,
        *,
        ignore_self: Optional[bool] = False,
        incident_id: Optional[str] = None,
        max_record_time: Optional[int] = None,
        min_record_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ):
        body = {
            "ignore_self": ignore_self,
            "incident_id": incident_id,
            "max_record_time": max_record_time,
            "min_record_time": min_record_time,
            "page": page,
            "entity_type_page_size": page_size,
        }
        # Filter None values
        body = {k: v for k, v in body.items() if v is not None}
        return self.api.incidents.history(body)

    """
    -------------COMMENTS API-------------
    """
    def create_comment(self, incident_id: str, text: str, markdown_to_html: bool = False):
        body = {
            "incident_id": incident_id,
            "markdown_to_html": markdown_to_html,
            "text": text
        }
        return self.comments.create(body)

    def delete_comment(self, comment_id: str):
        body = {
            "comment_id": comment_id
        }
        return self.comments.delete(body)
