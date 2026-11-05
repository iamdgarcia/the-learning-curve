"""
Brand assets — logo injection for Playwright pages.

Usage (works for both static screenshots and recorded animations):
    inject_logo(page)   # call after page.goto(), before screenshot/record

The logo is placed bottom-right, above the orange progress bar zone.
"""
from pathlib import Path

_LOGO = Path(__file__).parent.parent / "assets" / "logos" / "tlc_logo.png"

_JS = """(logoSrc) => {{
    const img = document.createElement('img');
    img.src = logoSrc;
    img.style.cssText = `
        position: fixed;
        bottom: 28px;
        right: 32px;
        width: 260px;
        opacity: 0.88;
        z-index: 99999;
        pointer-events: none;
    `;
    document.body.appendChild(img);
}}"""


def inject_logo(page) -> None:
    """Inject the TLC logo into a Playwright page (bottom-right, fixed)."""
    if not _LOGO.exists():
        return
    logo_uri = f"file://{_LOGO.resolve()}"
    page.evaluate(_JS, logo_uri)
