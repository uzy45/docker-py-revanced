"""Utilities."""
import os
import re
import subprocess
from typing import Dict

from loguru import logger
from requests import Response

from src.config import RevancedConfig
from src.exceptions import PatchingFailed

default_build = [
    "youtube",
    "youtube_music",
]
possible_archs = ["armeabi-v7a", "x86", "x86_64", "arm64-v8a"]


def update_changelog(name: str, response: Dict[str, str]) -> None:
    """Updated Changelog."""
    parent_repo = "https://github.com/nikhilbadyal/docker-py-revanced"
    with open("changelog.md", "a", encoding="utf_8") as file1:
        collapse_start = f"\n<details> <summary>👀 {name} </summary>\n\n"
        release_version = f"**Release Version** - [{response['tag_name']}]({response['html_url']})<br>"
        change_log = f"**Changelog** -<br> {response['body']}"
        publish_time = f"**Published at** -<br> {response['published_at']}"
        footer = f"<br><sub>Change logs generated by [Docker Py Revanced]({parent_repo})</sub>\n"
        collapse_end = "</details>"
        change_log = "".join(
            [
                collapse_start,
                release_version,
                change_log,
                publish_time,
                footer,
                collapse_end,
            ]
        )
        file1.write(change_log)


def handle_github_response(response: Response) -> None:
    """Handle Get Request Response."""
    response_code = response.status_code
    if response_code != 200:
        raise PatchingFailed(
            f"Unable to downloaded assets from GitHub. Reason - {response.text}"
        )


def slugify(string: str) -> str:
    """Converts a string to a slug format."""
    # Convert to lowercase
    modified_string = string.lower()

    # Remove special characters
    modified_string = re.sub(r"[^\w\s-]", "", modified_string)

    # Replace spaces with dashes
    modified_string = re.sub(r"\s+", "-", modified_string)

    # Remove consecutive dashes
    modified_string = re.sub(r"-+", "-", modified_string)

    # Remove leading and trailing dashes
    modified_string = modified_string.strip("-")

    return modified_string


def check_java(dry_run: bool) -> None:
    """Check if Java>=17 is installed."""
    try:
        if dry_run:
            return
        jd = subprocess.check_output(
            ["java", "-version"], stderr=subprocess.STDOUT
        ).decode("utf-8")
        jd = jd[1:-1]
        if "Runtime Environment" not in jd:
            raise subprocess.CalledProcessError(-1, "java -version")
        if "17" not in jd and "20" not in jd:
            raise subprocess.CalledProcessError(-1, "java -version")
        logger.debug("Cool!! Java is available")
    except subprocess.CalledProcessError:
        logger.error("Java>= 17 Must be installed")
        exit(-1)


def extra_downloads(config: RevancedConfig) -> None:
    """Download extra files."""
    from src.app import APP

    try:
        for extra in config.extra_download_files:
            url, file_name = extra.split("@")
            file_name_without_extension, file_extension = os.path.splitext(file_name)

            if file_extension.lower() != ".apk":
                logger.info(f"Only .apk extensions are allowed {file_name}.")
                continue

            new_file_name = f"{file_name_without_extension}-output{file_extension}"
            APP.download(url, config, assets_filter=".*apk", file_name=new_file_name)
    except (ValueError, IndexError):
        logger.info(
            "Unable to download extra file. Provide input in url@name.apk format."
        )
