"""Pydantic models for jarvis_package.yaml manifest files.

Ported from jarvis-node-setup/core/command_manifest.py.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from jdt.core.constants import SCHEMA_VERSION


class ManifestComponent(BaseModel):
    """A single component within a package bundle."""

    type: Literal[
        "command", "agent", "device_protocol", "device_manager",
        "prompt_provider", "routine",
    ]
    name: str
    path: str
    description: str = ""


class ManifestAuthor(BaseModel):
    github: str


class ManifestSecret(BaseModel):
    key: str
    scope: str
    value_type: str
    required: bool = True
    description: str = ""
    is_sensitive: bool = True
    friendly_name: str | None = None


class ManifestPackage(BaseModel):
    name: str
    version: str | None = None


class ManifestParameter(BaseModel):
    name: str
    param_type: str
    description: str | None = None
    required: bool = False
    default_value: Any | None = None
    enum_values: list[str] | None = None


class ManifestAuthentication(BaseModel):
    type: str
    provider: str
    friendly_name: str
    client_id: str
    keys: list[str]
    authorize_url: str | None = None
    exchange_url: str | None = None
    authorize_path: str | None = None
    exchange_path: str | None = None
    discovery_port: int | None = None
    discovery_probe_path: str | None = None
    scopes: list[str] = Field(default_factory=list)
    supports_pkce: bool = False
    native_redirect_uri: str | None = None


class CommandManifest(BaseModel):
    """Full manifest model matching jarvis_package.yaml schema."""

    schema_version: int = SCHEMA_VERSION

    # Core fields
    name: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    secrets: list[ManifestSecret] = Field(default_factory=list)
    packages: list[ManifestPackage] = Field(default_factory=list)
    parameters: list[ManifestParameter] = Field(default_factory=list)
    authentication: ManifestAuthentication | None = None

    # Author-provided metadata
    display_name: str = ""
    author: ManifestAuthor = Field(default_factory=lambda: ManifestAuthor(github=""))
    version: str = "0.1.0"
    min_jarvis_version: str = "0.9.0"
    license: str = "MIT"
    categories: list[str] = Field(default_factory=list)
    homepage: str = ""
    setup_guide: str = ""

    # Multi-component bundles
    components: list[ManifestComponent] = Field(default_factory=list)

    @property
    def is_bundle(self) -> bool:
        return len(self.components) > 1 or (
            len(self.components) == 1
            and self.components[0].type != "command"
        )
