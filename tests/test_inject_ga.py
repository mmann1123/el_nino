"""Pure-logic tests for the GA4 tag injection into Streamlit's index.html."""

from __future__ import annotations

from el_nino.dashboard import inject_ga


HTML = "<!DOCTYPE html>\n<html>\n  <head>\n    <title>x</title>\n  </head>\n</html>"


def test_patch_inserts_tag_inside_head():
    out = inject_ga.patch_html(HTML, "G-ABC1234567")
    assert "googletagmanager.com/gtag/js?id=G-ABC1234567" in out
    assert "gtag('config', 'G-ABC1234567')" in out
    # Inside <head>, before the original content.
    assert out.index("gtag") > out.index("<head>")
    assert out.index("gtag") < out.index("<title>")


def test_patch_is_idempotent():
    once = inject_ga.patch_html(HTML, "G-ABC1234567")
    twice = inject_ga.patch_html(once, "G-ABC1234567")
    assert once == twice
    assert once.count("googletagmanager") == 1


def test_patch_without_head_is_a_no_op():
    assert inject_ga.patch_html("<p>no head here</p>", "G-ABC1234567") == (
        "<p>no head here</p>"
    )


def test_main_no_ops_without_measurement_id(monkeypatch):
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    assert inject_ga.main() == 0


def test_main_rejects_malformed_id(monkeypatch, tmp_path):
    """A bad ID must not be written into the page as a JS string literal."""
    monkeypatch.setenv("GA_MEASUREMENT_ID", "'); alert(1); //")
    called = []
    monkeypatch.setattr(inject_ga, "streamlit_index", lambda: called.append(1))
    assert inject_ga.main() == 0
    assert not called


def test_main_survives_a_missing_streamlit_index(monkeypatch, tmp_path):
    """Analytics must never be the reason the container fails to boot."""
    monkeypatch.setenv("GA_MEASUREMENT_ID", "G-ABC1234567")
    monkeypatch.setattr(
        inject_ga, "streamlit_index", lambda: tmp_path / "nope" / "index.html"
    )
    assert inject_ga.main() == 0


def test_main_patches_the_file(monkeypatch, tmp_path):
    index = tmp_path / "index.html"
    index.write_text(HTML, encoding="utf-8")
    monkeypatch.setenv("GA_MEASUREMENT_ID", "G-ABC1234567")
    monkeypatch.setattr(inject_ga, "streamlit_index", lambda: index)
    assert inject_ga.main() == 0
    assert "G-ABC1234567" in index.read_text(encoding="utf-8")
