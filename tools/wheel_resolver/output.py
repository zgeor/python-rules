import urllib.request
import logging
import typing

_LOGGER = logging.getLogger(__name__)


def download(
    package_name: str,
    package_version: typing.Optional[str],
    url: typing.Tuple[str],
    download_out_name: str,
    download_out_metadata: str,
) -> bool:
    """Download url to $OUTS."""
    for u in url:
        try:
            urllib.request.urlretrieve(u, download_out_name)
        except urllib.error.HTTPError as error:
            _LOGGER.warning(
                f"download {package_name}-{package_version} from {u}: {error}",
            )
        finally:
            _LOGGER.info(f"downloaded {package_name}-{package_version} from {u}")
            with open(download_out_metadata, "w") as f:
                f.write(u)
            return True
    return False
