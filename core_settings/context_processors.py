
from .models import PharmacyProfile


def pharmacy_branding(request):
    """
    Make the saved pharmacy profile available
    in Django templates as `pharmacy`.

    Anonymous visitors can see the default
    brand label without initiating a database query.
    """
    default = {
        "name": "PharmaCare",
        "tagline": "Pharmacy Management System",
        "logo_url": "",
        "phone": "",
        "email": "",
        "address": "",
        "registration_number": "",
        "receipt_footer": "Thank you for shopping with us!",
        "currency_code": "PKR",
    }

    if not request.user.is_authenticated:
        return {"pharmacy": default}

    profile = (
        PharmacyProfile.objects
        .filter(pk=1)
        .first()
    )

    if profile is None:
        return {"pharmacy": default}

    logo_url = ""

    if profile.logo:
        try:
            logo_url = profile.logo.url
        except ValueError:
            pass

    return {
        "pharmacy": {
            "name": profile.name,
            "tagline": profile.tagline,
            "logo_url": logo_url,
            "phone": profile.phone,
            "email": profile.email,
            "address": profile.address,
            "registration_number": profile.registration_number,
            "receipt_footer": profile.receipt_footer,
            "currency_code": profile.currency_code,
        }
    }
