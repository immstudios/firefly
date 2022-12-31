from nxtools import get_guid
from pydantic import BaseModel, Field


class SiteConfiguration(BaseModel):
    """Site configuration model."""

    host: str = Field(..., title="Server url")
    name: str = Field(..., title="Site name")
    title: str | None = Field(None, title="Site title")
    token: str | None = Field(None, title="Access token")


class FireflyConfig(BaseModel):
    """Firefly configuration model."""

    client_id: str = Field(default_factory=get_guid, title="Client ID")
    debug: bool = Field(False, title="Debug mode")

    sites: list[SiteConfiguration] = Field(
        default_factory=list,
        title="Available sites",
    )

    site: SiteConfiguration | None = Field(
        None,
        title="Current site",
    )

    def set_site(self, index):
        """Set current site."""
        self.site = self.sites[index]


def get_config() -> FireflyConfig:
    """Get firefly configuration."""

    # TODO: Load from file.

    sites = [
        SiteConfiguration(name="nebula", host="http://localhost:4455"),
    ]

    return FireflyConfig(sites=sites)


config = get_config()
