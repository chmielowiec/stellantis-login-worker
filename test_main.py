import unittest

from main import AUTHORIZE_BUTTON_SELECTORS, extract_code, wait_for_code_or_authorize


class VisibleCandidate:
    async def is_visible(self):
        return True


class VisibleLocator:
    def __init__(self, candidate):
        self.candidate = candidate

    async def count(self):
        return 1

    def nth(self, _match_index):
        return self.candidate


class ConsentFrame:
    url = "https://id-dcr.peugeot.com/index/authorize-consentments"

    def __init__(self, candidate):
        self.candidate = candidate

    def locator(self, selector):
        if selector == "#consentbutton":
            return VisibleLocator(self.candidate)
        return VisibleLocator(None)


class Page:
    def __init__(self, url, frames=()):
        self.url = url
        self.frames = frames


class OAuthFlowTests(unittest.IsolatedAsyncioTestCase):
    def test_extracts_code_from_har_redirect(self):
        code = extract_code("mymap://oauth2redirect/pl?code=har-code&state=ignored")

        self.assertEqual(code, "har-code")

    async def test_direct_redirect_wins_without_checking_for_consent(self):
        page = Page("mymap://oauth2redirect/pl?code=har-code")

        code, authorize = await wait_for_code_or_authorize({"code": None}, page, 100)

        self.assertEqual(code, "har-code")
        self.assertIsNone(authorize)

    async def test_detects_only_explicit_consent_button(self):
        candidate = VisibleCandidate()
        page = Page("https://id-dcr.peugeot.com/index/authorize-consentments", [ConsentFrame(candidate)])

        code, authorize = await wait_for_code_or_authorize({"code": None}, page, 100)

        self.assertIsNone(code)
        self.assertEqual(authorize[1], candidate)
        self.assertEqual(AUTHORIZE_BUTTON_SELECTORS, ["#consentbutton"])


if __name__ == "__main__":
    unittest.main()