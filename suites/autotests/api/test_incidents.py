import datetime
import io
import logging
import random

import pytest_check as check
import ReceiveEmail, PDFWorker, wait_while, TEST_ENV_E2E
from constants.markers import *
import INCIDENTS_PRIORITY as PRIORITY
import INCIDENTS_RESOLUTION as RESOLUTION
import INCIDENTS_STATUS as STATUS

exclude_fields = ['update_time', 'was_read']

logger = logging.getLogger()


@wc_api
class TestApiIncidents:

    @pytest.mark.parametrize("priority", ["HIGH", "NORMAL", "LOW"])
    def test_incident_create(self, create_incident, mdr_api_manager, hive_api_manager, priority):
        created_incident = create_incident(priority=priority)

        check.equal(created_incident['priority'], priority)
        incidents_page = mdr_api_manager.get_list_incidents(page_size=10, max_page=1,
                                                            additional_body={
                                                                "search_phrase":
                                                                    str(created_incident['incident_number'])})
        incident = [incident for incident in incidents_page
                    if incident["incident_number"] == created_incident['incident_number']][0]

        check.is_true(all(created_incident[field] == incident[field] for field in created_incident
                          if field not in exclude_fields))

    def test_get_incident_count(self, mdr_api_manager):
        # Incidents list max 10000. Elastic restriction
        count = mdr_api_manager.get_incident_count()

        all_incidents = mdr_api_manager.get_all_incidents
        check.greater_equal(count, len(all_incidents))

    def test_incident_close(self, create_incident, mdr_api_manager, hive_api_manager):
        created_incident = create_incident()
        incident_id = created_incident['incident_id']
        mdr_api_manager.close_incident(incident_id=incident_id, summary="Test", resolution_status="FALSE_POSITIVE")

        incidents_page = mdr_api_manager.get_list_incidents(max_page=1,
                                                            additional_body={
                                                                "search_phrase":
                                                                    str(created_incident['incident_number'])})
        incident_close = [incident for incident in incidents_page
                          if incident["summary"] == created_incident['summary']][0]

        check.equal(incident_close['incident_id'], incident_id)
        check.equal(incident_close['resolution'], "False positive")
        check.equal(incident_close['status'], "Closed")
        check.equal(incident_close['status_description'], "Test")

    def test_get_incident_details(self, create_incident, mdr_api_manager, hive_api_manager):
        created_incident = create_incident()
        incident_id = created_incident["incident_id"]
        details = mdr_api_manager.get_incident_details(incident_id=incident_id)

        check.is_true(all(created_incident[field] == details[field]
                          for field in created_incident if field not in exclude_fields),
                      f"Check create incident {created_incident}, details incident {details}")

    def test_get_incident_history(self, create_incident, mdr_api_manager, hive_api_manager):
        exclude_history = ['update_time', 'attachments', 'comments', 'responses']
        incident_creating = create_incident()
        incident_id = incident_creating['incident_id']
        incident_history = mdr_api_manager.get_incidents_history(incident_id=incident_id)

        check.equal(incident_history[0]['entity']['incident_details']['priority'], 'HIGH')

        check.is_true(all(incident_creating[field] == incident_history[0]['entity']['incident_details'][field]
                          for field in incident_creating if field not in exclude_history))

    @pytest.mark.parametrize("page_size", [10, 50, 100])
    def test_get_incident_list_page(self, mdr_api_manager, hive_api_manager, page_size):
        incident_list = mdr_api_manager.get_list_incidents(page_size=page_size, max_page=1)
        check.equal(len(incident_list), page_size)

    def test_get_incident_list_all_fields(self, mdr_api_manager, hive_api_manager):
        all_fields = ['incident_id', 'summary', 'priority', 'status', 'resolution', 'affected_hosts',
                      'affected_hosts_mappings', 'host_based_iocs', 'network_based_iocs', 'detection_technology',
                      'creation_time', 'update_time', 'attack_stage', 'mitre_tactics', 'mitre_techniques',
                      'description', 'incident_number', 'client_description', 'status_description', 'origin',
                      'attachments', 'comments', 'iocs', 'responses', 'tenant_name', 'was_read']
        incident_list = mdr_api_manager.get_list_incidents(page_size=10, max_page=1)
        incident_random_zero = random.choice(incident_list)

        incident_list_fields = mdr_api_manager.get_list_incidents(page_size=10,
                                                                  max_page=1,
                                                                  additional_body={"fields": all_fields})
        incident_random_fields = random.choice(incident_list_fields)

        check.equal(incident_random_zero.keys(), incident_random_fields.keys())

    def test_incident_send_email(self, mdr_api_manager):
        incident_list = mdr_api_manager.get_list_incidents(page_size=100, max_page=1)
        incident_random = random.choice(incident_list)
        incident_number = str(incident_random['incident_number'])
        incident_priority = incident_random["priority"]
        incident_status = incident_random["status"]
        incident_resolution = incident_random["resolution"]
        with ReceiveEmail() as email:
            unseen_mail_before = email.get_unseen_email()

            mdr_api_manager.incident_send_email(issue_key=incident_number,
                                                issue_type="thehive",
                                                user_email=TEST_ENV_E2E.mdr_login)

            assert wait_while(lambda: set(email.get_unseen_email()) - set(unseen_mail_before) == set(),
                              timeout=10 * 60, delay=10), f'Email was not received'

            unseen_mails = email.get_unseen_email()
            logger.info(unseen_mails)
            for mail in unseen_mails[::-1]:
                file_mail = email.get_email_content(mail)
                if file_mail.get("Attach") == f'K-{incident_number}.pdf':
                    check.is_in('[Incident] MDR report', file_mail['Subject'],
                                f'mail received subject {file_mail["Subject"]}')
                    check.is_in('soc-no-reply@kaspersky.com', file_mail['From'],
                                f'mail received from {file_mail["From"]}')
                    check.is_in(TEST_ENV_E2E.mdr_login, file_mail['To'], f'mail received To {file_mail["To"]}')

                    pdf_file = io.BytesIO(file_mail['Attach_content'])
                    pdf = PDFWorker(pdf_file)
                    extracted_text = pdf.extract_text().replace("\n", '')
                    time = datetime.datetime.fromtimestamp(incident_random['creation_time'] / 1000,
                                                           tz=datetime.timezone.utc).strftime('%d.%m.%Y %H:%M')

                    values_to_check_is_in = [f"K-{incident_number}", incident_random["summary"], "Решение:",
                                             "Статус:", 'Приоритет инцидента:', PRIORITY[incident_priority],
                                             STATUS[incident_status], RESOLUTION[incident_resolution], time,
                                             incident_random['affected_hosts'][0].split(":")[0]]

                    for value in values_to_check_is_in:
                        check.is_in(value, extracted_text, f"{value} not in received PDF")
                    break
            else:
                pytest.fail(f'Mail K-{incident_number} was not found')

    @pytest.mark.skip("No realizations")
    def test_incident_sla_count(self, mdr_api_manager):
        # TODO создание нового клиента
        incident_sla = mdr_api_manager.get_incident_sla_count()['limit']
        assert incident_sla == 3
