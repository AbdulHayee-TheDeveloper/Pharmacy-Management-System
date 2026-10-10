
from .models import PharmacyProfile


def pharmacy_branding(request):
    """
    Provide global pharmacy branding and branch mode
    to authenticated users' templates.

    Context variables:
        pharmacy
        multi_branch_enabled
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
        "enable_multi_branch": False,
    }

    if not request.user.is_authenticated:
        return {
            "pharmacy": default,
            "multi_branch_enabled": False,
        }

    profile = (
        PharmacyProfile.objects
        .filter(pk=1)
        .first()
    )

    if profile is None:
        return {
            "pharmacy": default,
            "multi_branch_enabled": False,
        }

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
            "enable_multi_branch": profile.enable_multi_branch,
        },
        "multi_branch_enabled": profile.enable_multi_branch,
    }
