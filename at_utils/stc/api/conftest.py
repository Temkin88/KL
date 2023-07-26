import logging
from random import choice
from typing import List
from uuid import uuid4

import pytest


@pytest.fixture(scope="class")
def create_incident(mdr_api_manager, hive_api_manager):
    created_incidents = []

    def _get_affected_hosts() -> List[str]:
        """
        Get random host from assets
        :return: List of 1 affected host
        """
        asset = choice(mdr_api_manager.get_all_assets)
        return [f"{asset['host_name']}:{asset['asset_id']}"]

    def _create_incident(priority='HIGH'):
        """
        Create incident with random affected hosts
        :return: Created incident
        """
        incident_hex = uuid4().hex
        logging.info(f"creating incident {incident_hex}")
        affected_hosts = _get_affected_hosts()
        incident = mdr_api_manager.create_incident(affected_hosts=affected_hosts,
                                                   client_description=f"test_client_description_{incident_hex}",
                                                   summary=f"API_test_{incident_hex}",
                                                   priority=priority)
        created_incidents.append(incident)
        return incident

    yield _create_incident

    # Force delete all created incidents
    for incident in created_incidents:
        logging.info(f"deleting incident {incident['incident_id']}")
        hive_api_manager.delete_case(incident["incident_id"], force=True)


@pytest.fixture(scope="class")
def create_comment(mdr_api_manager, create_incident):
    created_comments = []

    def _create_comment(incident_id: int, comment_text: str):
        logging.info(f"creating comment {comment_text}")
        comment = mdr_api_manager.create_comment(incident_id=incident_id, text=comment_text)
        created_comments.append(comment)
        return comment

    yield _create_comment

    for comment in created_comments:
        logging.info(f"delete comment {comment['comment_id']}")
        mdr_api_manager.delete_comment(comment["comment_id"])
