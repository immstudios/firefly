from pydantic import BaseModel, Field


class SiteConfiguration(BaseModel):
    """Site configuration model."""

    site_name: str = Field("nebula", title="Site name")
    host: str = Field("http://localhost:4455", title="Server url")
    token: str | None = Field(None, title="Access token")


class FireflyConfig(BaseModel):
    """Firefly configuration model."""

    sites: list[SiteConfiguration] = Field(
        default_factory=list,
        title="Available sites",
    )

    site: SiteConfiguration | None = Field(
        None,
        title="Current site",
    )
