from typing import Literal


def download_text(url: str, type: Literal["json", "text"] = "json"):
    import httpx

    from xrouter.gwlib import gw

    try:
        resp = httpx.get(url)
        resp.raise_for_status()
        if type == "json":
            return resp.json()
        elif type == "text":
            return resp.text
    except Exception as e:
        gw.logger.error(f"Failed to download {url}", exc_info=e)
