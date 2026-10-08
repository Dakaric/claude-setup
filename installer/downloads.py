import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


class DownloadError(RuntimeError):
    pass


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        redirected = super().redirect_request(request, fp, code, message, headers, new_url)
        if redirected and urlsplit(request.full_url).hostname != urlsplit(new_url).hostname:
            redirected.remove_header("Authorization")
        return redirected


def download(url: str, target: Path) -> None:
    headers = {"User-Agent": "claude-setup"}
    if urlsplit(url).hostname in {"api.github.com", "github.com", "raw.githubusercontent.com"}:
        if token := os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    # Weiterleitungen dürfen den GitHub-Token nicht an fremde Hosts weitergeben.
    opener = urllib.request.build_opener(SafeRedirectHandler())
    previous = urllib.request._opener
    try:
        urllib.request.install_opener(opener)
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 403 and error.headers.get("X-RateLimit-Remaining") == "0":
            raise DownloadError("GitHub-Rate-Limit erreicht. Später erneut starten oder GITHUB_TOKEN setzen.") from error
        raise DownloadError(f"Download fehlgeschlagen (HTTP {error.code}): {url}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise DownloadError(f"Download fehlgeschlagen: {url}. Verbindung prüfen und erneut starten.") from error
    finally:
        urllib.request.install_opener(previous)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
