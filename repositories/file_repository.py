import os
import json

class FileRepository:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir

    def get_policies_path(self) -> str:
        return os.path.join(self.base_dir, "policies.json")

    def get_products_path(self) -> str:
        return os.path.join(self.base_dir, "products.json")

    def load_policies(self) -> list:
        path = self.get_policies_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                policies = json.load(f)
            for p in policies:
                p["metadata"] = {"type": "policy"}
            return policies
        return []

    def load_products(self) -> list:
        path = self.get_products_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                products = json.load(f)
            for p in products:
                p["metadata"] = {"type": "product"}
            return products
        return []

    def save_products(self, products_data: list) -> None:
        path = self.get_products_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
