import logging
import random

import pytest_check as check
from at_utils.constants.markers import *

logger = logging.getLogger()

MIN_ASSETS_NUM = 10


@wc_api
class TestApiAssets:
    """
        :param uuid: a1db26d6-bdc2-4252-9439-4e3c300872c8
    """
    def test_get_all_assets(self, mdr_api_manager):
        assets = mdr_api_manager.get_all_assets
        assert len(assets) >= MIN_ASSETS_NUM

    def test_get_assets_count(self, mdr_api_manager):
        assets = mdr_api_manager.get_all_assets
        asset_random = random.choice(assets)
        host_name = asset_random['host_name']
        assets_name = mdr_api_manager.get_assets_by_hostname(host_name)

        count = mdr_api_manager.get_assets_count()
        check.equal(len(assets), count, f"Expected: {len(assets)} assets, result: {count} assets")

        count_host_name = mdr_api_manager.get_assets_count(body={"host_names": [host_name]})
        check.equal(len(assets_name), count_host_name), \
            f"Expected: {len(assets_name)} assets, result: {count_host_name} assets with hostname {host_name}"

    def test_get_asset_details(self, mdr_api_manager):
        fields_to_check = ["asset_id", "host_name", "first_seen", "last_seen", "installed_product_info", "ksc_host_id",
                           "isolation", "status"]

        assets = mdr_api_manager.get_all_assets
        asset_random = random.choice(assets)
        details_asset_id = mdr_api_manager.get_assets_details(assets_id=asset_random["asset_id"], fields=["asset_id"])
        check.is_true(details_asset_id.keys() == {"asset_id"}, f"Expected fields: ['asset_id'], "
                                                               f"result: {details_asset_id.keys()}")
        assert asset_random["asset_id"] == details_asset_id['asset_id']

        asset_details = mdr_api_manager.get_assets_details(assets_id=asset_random["asset_id"])
        assert all(asset_random[field] == asset_details[field] for field in fields_to_check)

    def test_get_assets_suggestion(self, mdr_api_manager):
        assets = mdr_api_manager.get_all_assets
        asset_random = random.choice(assets)
        host_name = asset_random['host_name'].split("-")[0]
        suggestions_list = mdr_api_manager.get_assets_suggestion(search_phrase=host_name)
        assert len(suggestions_list) != 0, "No assets were found"
        assert all([host_name in suggestion for suggestion in suggestions_list])



