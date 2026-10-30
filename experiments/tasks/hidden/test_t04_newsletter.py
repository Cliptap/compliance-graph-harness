import re


def test_newsletter_consent_is_not_prechecked(client):
    page = client.get("/newsletter").text
    assert 'name="consent"' in page
    assert not re.search(r'<input[^>]*name="consent"[^>]*checked|<input[^>]*checked[^>]*name="consent"',
                         page, re.IGNORECASE)
