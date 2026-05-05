from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicApi:
    name: str
    purpose: str
    url: str


VERIFIED_PUBLIC_APIS: tuple[PublicApi, ...] = (
    PublicApi("HTTPBin", "HTTP debugging and request inspection", "https://httpbin.org/get"),
    PublicApi("JSONPlaceholder", "Fake REST resources for testing", "https://jsonplaceholder.typicode.com/posts"),
    PublicApi("IPify", "Public IP lookup", "https://api.ipify.org?format=json"),
    PublicApi("ip-api", "IP geolocation and network context", "http://ip-api.com/json/"),
    PublicApi("REST Countries", "Country and region metadata", "https://restcountries.com/v3.1/all"),
    PublicApi("RandomUser", "Synthetic user/profile generation", "https://randomuser.me/api/"),
    PublicApi("DuckDuckGo Instant Answer API", "Lightweight public search and knowledge lookup", "https://api.duckduckgo.com/?q=example&format=json"),
)


def render_api_catalog() -> str:
    return "\n".join(f"- {api.name}: {api.purpose} ({api.url})" for api in VERIFIED_PUBLIC_APIS)
