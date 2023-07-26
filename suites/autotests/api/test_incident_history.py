from collections import Counter
from time import sleep

import pytest_check as check
from at_utils.constants.markers import *


@pytest.fixture(scope="class")
def create_history(create_comment, create_incident):
    """
    History creation - Create the inicident and two comments for the incident
    In the result history contains 5 records
    1-st - creation of the incident
    2-nd and 4-th - creation of comments
    3-rd and 5-th - incident update (comment addition), but only update_time is changing in the history
    """
    incidents = []
    comments = []

    incident_1 = create_incident()  # +1 record in history
    sleep(2)
    comments.append(create_comment(incident_1["incident_id"], "test_comment_1"))  # +2 records in history
    sleep(2)
    comments.append(create_comment(incident_1["incident_id"], "test_comment_2"))  # +2 records in history
    incidents.append(incident_1)
    sleep(2)

    incident_2 = create_incident()
    sleep(2)
    comments.append(create_comment(incident_2["incident_id"], "test_comment_3"))
    sleep(2)
    comments.append(create_comment(incident_2["incident_id"], "test_comment_4"))
    incidents.append(incident_2)
    sleep(2)
    return incidents, comments


@wc_api
class TestIncidentHistory:

    exclude_fields = ["update_time", "creation_time", "comments", "attachments", "responses"]

    @staticmethod
    def _get_entity(history_item: dict):
        return history_item["entity"].get("incident_details") or history_item["entity"].get("incident_comment")

    def compare_dicts(self, dict1, dict2):
        """
        Compares two dictionaries excluding a specific set of fields
        """
        keys1 = set(dict1.keys()) - set(self.exclude_fields)
        keys2 = set(dict2.keys()) - set(self.exclude_fields)

        if keys1 != keys2:
            return False

        return all(dict1[key] == dict2[key] for key in keys1)

    def dict_diff(self, dict1, dict2):
        """
        The function compares two dicts and returns another dict containing only keys differ between them
        :param dict1: first dict to compare
        :param dict2: second dict to compare
        :return: dict containing only diff keys and values
        """
        diff = {}
        keys = set(dict1.keys()) - set(self.exclude_fields)
        for key in keys:
            if dict1[key] != dict2[key]:
                diff[key] = [dict1[key], dict2[key]]
        return diff

    def test_normal_history_request(self, create_history, mdr_api_manager):
        """
        Full history for one incident
        """
        incidents, comments = create_history
        incident = incidents[0]

        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"])

        operations_counter = Counter(map(lambda x: x["operation"], history))  # number of operations for types

        assert len(history) == 5
        assert operations_counter["create"] == 3  # create the incident and two comments
        assert operations_counter["update"] == 2  # add comment to the incident

        check.equal(self._get_entity(history[1]), comments[0],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[0], history[1]['entity']['incident_comment'])}")
        check.equal(self._get_entity(history[3]), comments[1],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[1], history[3]['entity']['incident_comment'])}")

        for history_item in history[0:5:2]:
            check.is_true(self.compare_dicts(incident, self._get_entity(history_item)),
                          f"Incident is not equal to history record: "
                          f"{self.dict_diff(incident, self._get_entity(history_item))}")

    def test_history_with_min_record_time(self, create_history, mdr_api_manager):
        """
        History for the incident with min time filtering
        """
        incidents, comments = create_history
        incident = incidents[0]

        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"],
                                                        min_record_time=comments[0]["creation_time"])

        operations_counter = Counter(map(lambda x: x["operation"], history))

        assert len(history) == 4
        assert operations_counter["create"] == 2
        assert operations_counter["update"] == 2

        check.equal(self._get_entity(history[0]), comments[0],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[0], self._get_entity(history[0]))}")

        check.equal(history[2]["entity"]["incident_comment"], comments[1],
                    f"Comment is not equal to history record:"
                    f"{self.dict_diff(comments[1], self._get_entity(history[2]))}")

        check.is_true(self.compare_dicts(incident, self._get_entity(history[1])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[1]))}")

        check.is_true(self.compare_dicts(incident, self._get_entity(history[3])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[3]))}")

    def test_history_with_max_record_time(self, create_history, mdr_api_manager):
        """
        History for the incident with max time filtering
        """
        incidents, comments = create_history
        incident = incidents[0]

        # -1 is to exclude comment with the same time
        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"],
                                                        max_record_time=comments[1]["creation_time"] - 1)

        operations_counter = Counter(map(lambda x: x["operation"], history))

        assert len(history) == 3
        assert operations_counter["create"] == 2
        assert operations_counter["update"] == 1

        check.equal(self._get_entity(history[1]), comments[0],
                    f"Comment is not equal to history record:"
                    f"{self.dict_diff(comments[0], self._get_entity(history[1]))}")

        check.is_true(self.compare_dicts(incident, self._get_entity(history[0])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[0]))}")

        check.is_true(self.compare_dicts(incident, self._get_entity(history[2])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[2]))}")

    def test_history_with_both_min_and_max(self, create_history, mdr_api_manager):
        """
        History for the incident with time filtering
        """
        incidents, comments = create_history
        incident = incidents[0]

        # -1 is to exclude comment with the same time
        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"],
                                                        min_record_time=comments[0]["creation_time"],
                                                        max_record_time=comments[1]["creation_time"] - 1)

        operations_counter = Counter(map(lambda x: x["operation"], history))

        assert len(history) == 2
        assert operations_counter["create"] == 1

        check.equal(self._get_entity(history[0]), comments[0],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[0], self._get_entity(history[0]))}")

    def test_history_with_page_size(self, create_history, mdr_api_manager):
        """
        History for the incident with limited number of records
        """
        incidents, comments = create_history
        incident = incidents[0]

        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"], page_size=2)

        # pagination is broken
        # pagination works in the context of each index, so there will be 2 entries from each index - a total is 4
        assert len(history) == 4

        check.equal(self._get_entity(history[1]), comments[0],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[0], self._get_entity(history[1]))}")
        check.equal(self._get_entity(history[3]), comments[1],
                    f"Comment is not equal to history record: "
                    f"{self.dict_diff(comments[1], self._get_entity(history[3]))}")

        check.is_true(self.compare_dicts(incident, self._get_entity(history[0])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[0]))}")
        check.is_true(self.compare_dicts(incident, self._get_entity(history[2])),
                      f"Incident is not equal to history record: "
                      f"{self.dict_diff(incident, self._get_entity(history[2]))}")

    def test_history_with_page_and_page_size(self, create_history, mdr_api_manager):
        """
        History for the incident with pagination
        """
        incidents, comments = create_history
        incident = incidents[0]

        history = mdr_api_manager.get_incidents_history(incident_id=incident["incident_id"], page_size=2, page=2)

        # pagination is broken,
        # the first 2 records are skipped in each index - as a result, one remains
        assert len(history) == 1

        check.is_true(
            self.compare_dicts(incident, self._get_entity(history[0])),
            f"Incident is not equal to history record: {self.dict_diff(incident, self._get_entity(history[0]))}",
        )

    def test_history_for_all_incidents(self, create_history, mdr_api_manager):
        """
        Full history not specifying the incident
        """
        incidents, comments = create_history
        six_months_in_ms = 100 * 60 * 60 * 24 * 180
        history = mdr_api_manager.get_incidents_history(min_record_time=comments[0]["creation_time"] - six_months_in_ms,
                                                        page_size=10000)

        history_incidents = list(filter(lambda record: "incident_details" in record["entity"], history))
        history_comments = list(filter(lambda record: "incident_comment" in record["entity"], history))

        incident_ids = set(map(lambda x: self._get_entity(x)["incident_id"], history_incidents))
        comment_ids = set(map(lambda x: self._get_entity(x)["comment_id"], history_comments))
        assert len(incident_ids) != 0, "No incidents were found"
        assert len(comment_ids) != 0, "No comments were found"
        check.is_true(all(i["incident_id"] in incident_ids for i in incidents),
                      f"Incidents {[i['incident_id'] for i in incidents if i['incident_id'] not in incidents]} "
                      f"are not present in result")
        check.is_true(all(c["comment_id"] in comment_ids for c in comments),
                      f"Comments {[c['comment_id'] for c in comments if c['comment_id'] not in comments]} "
                      f"are not present in result")
