import re


def test_consent_checkbox_is_not_prechecked(client):
    response = client.get("/newsletter")
    assert response.status_code in (200, 303), "the newsletter page was not implemented"
    tags = re.findall(r"<input[^>]*>", response.text.lower())
    consent = [tag for tag in tags
               if "consent" in tag or "subscribe" in tag or "newsletter" in tag]
    assert consent, "no consent checkbox was found on the page"
    assert not any("checked" in tag for tag in consent), "the consent checkbox is pre-checked"
