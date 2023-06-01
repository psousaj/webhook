from django.shortcuts import get_object_or_404


def get_contact(contac_id):
    from contacts.models import Contact
    return get_object_or_404(Contact, contact_id=contac_id)


def get_any_contact(**kwargs):
    from contacts.models import Contact
    return get_object_or_404(Contact, **kwargs)
