import requests


class APIClient:
    DEFAULT_TIMEOUT = 5

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_products(self) -> requests.Response:
        return self.session.get(self._url("/products"), timeout=self.DEFAULT_TIMEOUT)

    def get_product(self, product_id: int) -> requests.Response:
        return self.session.get(
            self._url(f"/products/{product_id}"), timeout=self.DEFAULT_TIMEOUT
        )

    def get_orders(self) -> requests.Response:
        return self.session.get(self._url("/orders"), timeout=self.DEFAULT_TIMEOUT)

    def get_order(self, order_id: int) -> requests.Response:
        return self.session.get(
            self._url(f"/orders/{order_id}"), timeout=self.DEFAULT_TIMEOUT
        )

    def create_order(self, payload: dict) -> requests.Response:
        return self.session.post(
            self._url("/orders"), json=payload, timeout=self.DEFAULT_TIMEOUT
        )

    def get_users(self) -> requests.Response:
        return self.session.get(self._url("/users"), timeout=self.DEFAULT_TIMEOUT)

    def get_user(self, user_id: int) -> requests.Response:
        return self.session.get(
            self._url(f"/users/{user_id}"), timeout=self.DEFAULT_TIMEOUT
        )

    def health_check(self) -> requests.Response:
        return self.session.get(self._url("/health"), timeout=self.DEFAULT_TIMEOUT)
