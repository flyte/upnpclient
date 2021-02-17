import unittest

import upnpclient as upnp


class TestErrors(unittest.TestCase):
    desc = upnp.errors.ERR_CODE_DESCRIPTIONS

    def test_existing_err(self):
        for key, value in self.desc._descriptions.items():
            self.assertEqual(self.desc[key], value)

    def test_non_integer(self):
        try:
            self.desc["a string"]
            raise Exception("Should have raised KeyError.")
        except KeyError as exc:
            self.assertEqual(str(exc), "\"'key' must be an integer\"")

    def test_reserved(self):
        for i in range(606, 612 + 1):  # 606-612
            self.assertEqual(
                self.desc[i], "These ErrorCodes are reserved for UPnP DeviceSecurity."
            )

    def test_common_action(self):
        for i in range(613, 699 + 1):
            self.assertEqual(
                self.desc[i],
                "Common action errors. Defined by UPnP Forum Technical Committee.",
            )

    def test_action_specific_committee(self):
        for i in range(700, 799 + 1):
            self.assertEqual(
                self.desc[i],
                "Action-specific errors defined by UPnP Forum working committee.",
            )

    def test_action_specific_vendor(self):
        for i in range(800, 899 + 1):
            self.assertEqual(
                self.desc[i],
                "Action-specific errors for non-standard actions. Defined by UPnP vendor.",
            )
