
from django.shortcuts import get_object_or_404
from contacts.get_objects import get_contact


def get_pendencies(contact_id, **kwargs):
    contact = get_contact(contac_id=contact_id)

    return contact.get_pendencies()
