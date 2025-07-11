
import huggingface_hub
from huggingface_hub import ModelCard, list_models, HfApi

class HF_API:
    def __init__(self, hf_token, sort='downloads', model_limit=50):
        self.hf_token = hf_token
        self.sort = sort
        self.model_limit = model_limit
        self.api = HfApi(token=hf_token)

    def get_models(self):
        for model in list_models(sort=self.sort, limit=self.model_limit, token=self.hf_token):
            yield model.id

    def get_model_details(self, model_id):
        return self.api.model_info(repo_id=model_id)

    def get_model_card_data(self, model_id):
        try:
            card = ModelCard.load(model_id, token=self.hf_token)
            return card.data.to_dict()
        except Exception:
            return {}

    def get_base_models(self, model_id):
        card_data = self.get_model_card_data(model_id)
        base_models = card_data.get("base_model", [])
        if isinstance(base_models, str):
            return [base_models]
        elif isinstance(base_models, list):
            return base_models
        return []

    def get_license_info(self, model_id):
        card_data = self.get_model_card_data(model_id)
        return {
            "license": card_data.get("license", ""),
            "license_name": card_data.get("license_name", ""),
            "license_link": card_data.get("license_link", "")
        }

if __name__ == "__main__":
    hf_api = HF_API("[YOUR_TOKEN]")
    for model_id in hf_api.get_models():
        print(model_id)
