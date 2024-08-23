import click
import typing
import logging
import click_log
import sys
import tools.wheel_resolver.wheel as wheel
import tools.wheel_resolver.output as output
import packaging.tags as tags
import distlib.locators
import itertools
import os
import urllib.request

_LOGGER = logging.getLogger(__name__)

click_log.basic_config(_LOGGER)


@click.command()
@click.option(
    "--url",
    "--urls",
    multiple=True,
    metavar="URL",
    default=[],
    help="URLs to check for package before looking in the wheel index",
)
@click.option(
    "--package-name",
    "--package",
    metavar="NAME",
    required=True,
    help="Name of Python package in PyPI",
)
@click.option(
    "--package-version",
    "--version",
    metavar="VERSION",
    help="Version of Python package in PyPI",
)
@click.option(
    "--interpreter",
    default={t.interpreter for t in tags.sys_tags()},
    multiple=True,
    metavar="INTERPRETER",
    show_default=True,
    help="The interpreter name or abbreviation code with version, for example py31 or cp310",
)
@click.option(
    "--platform",
    # Must cast to list so click knows we want multiple default values.
    default={t.platform for t in tags.sys_tags()},
    metavar="PLATFORM",
    multiple=True,
    help="The platform identifier, for example linux_x86_64 or linux_i686",
)
@click.option(
    "--abi",
    default={t.abi for t in tags.sys_tags()},
    metavar="ABI",
    show_default=True,
    multiple=True,
    help="The ABI identifier, for example cp310 or abi3",
)
@click.option(
    "--output-whl-name",
    metavar="OUTS_WHL_NAME",
    show_default=False,
    multiple=False,
    help="The output wheel name.",
)
@click.option(
    "--output-whl-metadata-name",
    metavar="OUTS_WHL_META_NAME",
    show_default=False,
    multiple=False,
    help="The of the output metadata file. If not specified the file will not be produced.",
)
@click.option(
    "--prereleases",
    default=False,
    metavar="PRERELEASES",
    show_default=True,
    multiple=False,
    help="Whether prereleased wheels should also be downloaded",
)
@click_log.simple_verbosity_option(_LOGGER)
def main(
    url: typing.Tuple[str],
    package_name: str,
    package_version: typing.Optional[str],
    interpreter: typing.Tuple[str, ...],
    platform: typing.Tuple[str, ...],
    abi: typing.Tuple[str, ...],
    output_whl_name: str | None,
    output_whl_metadata_name: str,
    prereleases: bool = False,
):
    """Resolve a wheel by name and version to a URL.

    If URLs are specified, they are checked literally before doing a lookup in
    PyPI for PACKAGE with VERSION.

    """

    if not output_whl_name:
        _LOGGER.warning("Fallback on using deprecated env variable '$OUTS'.")
        output_whl_name = os.getenv("OUTS")

    if not output_whl_name:
        _LOGGER.error("Neither '--output-whl-name' or env:$OUTS is specified.")
        sys.exit(1)

    locator = distlib.locators.SimpleScrapingLocator(url="https://pypi.org/simple")
    locator.wheel_tags = list(itertools.product(interpreter, abi, platform))
    try:
        pypi_url = wheel.url(
            package_name=package_name,
            package_version=package_version,
            tags=[
                str(x)
                for i in interpreter
                for x in tags.generic_tags(
                    interpreter=i,
                    abis=set(abi),
                    platforms=set(platform).union({"any"}),
                )
            ],
            locator=locator,
            prereleases=prereleases,
        )
    except Exception as error:
        _LOGGER.error(error)
        _LOGGER.error(f"could not find PyPI URL for {package_name}-{package_version}")
        sys.exit(1)

    try:
        urllib.request.urlretrieve(pypi_url, output_whl_name)
        _LOGGER.info(f"downloaded {package_name}-{package_version} from {u}")

        if output_whl_metadata_name != "":
            with open(output_whl_metadata_name, "w") as f:
                f.write(pypi_url)
        else:
            _LOGGER.info("Not generating metadata file, as name not defined.")
    except urllib.error.HTTPError as error:
        _LOGGER.warning(f"download {package_name}-{package_version} from {u}: {error}")
        sys.exit(1)
