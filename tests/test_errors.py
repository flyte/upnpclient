import pytest
import upnpclient


desc = upnpclient.errors.ERR_CODE_DESCRIPTIONS


def test_existing_error_codes():
    for key, value in desc._descriptions.items():
        assert desc[key] == value


def test_non_integer_key():
    with pytest.raises(KeyError, match="'key' must be an integer"):
        desc["a string"]


def test_reserved_range():
    for i in range(606, 613):
        assert desc[i] == "These ErrorCodes are reserved for UPnP DeviceSecurity."


def test_common_action_range():
    for i in range(613, 700):
        assert desc[i] == "Common action errors. Defined by UPnP Forum Technical Committee."


def test_committee_range():
    for i in range(700, 800):
        assert desc[i] == "Action-specific errors defined by UPnP Forum working committee."


def test_vendor_range():
    for i in range(800, 900):
        assert desc[i] == "Action-specific errors for non-standard actions. Defined by UPnP vendor."
