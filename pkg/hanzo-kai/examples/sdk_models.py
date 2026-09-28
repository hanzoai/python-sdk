from hanzo_kai import Kai

with Kai() as kai:
    for model in kai.models.list():
        print(model.id, model.owned_by, model.pricing.input, model.pricing.output)
