import httpx
from spaceship_cli.config import settings

class SpaceshipClient:
    def __init__(self):
        self.base_url = settings.base_url
        self.headers = {
            "X-Api-Key": settings.api_key,
            "X-Api-Secret": settings.api_secret,
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        with httpx.Client() as client:
            response = client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    def _post(self, endpoint: str, json: dict = None):
        url = f"{self.base_url}{endpoint}"
        with httpx.Client() as client:
            response = client.post(url, headers=self.headers, json=json)
            response.raise_for_status()
            return response.json()

    def list_domains(self, limit: int = 10, offset: int = 0):
        """
        List domains.
        Note: Adjust endpoint based on actual API docs if different from /domains.
        Ref: https://docs.spaceship.dev/
        """
        # Based on standard REST patterns, assuming /domains.
        # I will check exact path if needed, but assuming /domains for now as placeholder.
        return self._get("/domains", params={"take": limit, "skip": offset})

    def list_dns_records(self, domain: str, limit: int = 100, offset: int = 0, order_by: str = None):
        """
        List DNS records for a domain.
        Endpoint: GET /v1/dns/records/{domain}
        """
        params = {"take": limit, "skip": offset}
        if order_by:
            params["orderBy"] = order_by
        return self._get(f"/dns/records/{domain}", params=params)

    def get_domain_info(self, domain: str):
        """
        Get domain info.
        Endpoint: GET /v1/domains/{domain}
        """
        return self._get(f"/domains/{domain}")

    def list_contacts(self, limit: int = 10, offset: int = 0):
        """
        List contacts.
        Endpoint: GET /v1/contacts
        """
        return self._get("/contacts", params={"take": limit, "skip": offset})

    def check_availability(self, domains: list[str]):
        """
        Check domains availability.
        Endpoint: POST /v1/domains/available
        Body: {"domains": ["example.com", ...]}
        """
        return self._post("/domains/available", json={"domains": domains})
