from .content import INSURERS


def insurance_providers(request):
    return {"insurers": INSURERS}
