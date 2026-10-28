"""INERT NEGATIVE SECURITY PROBE. Never import, execute or merge this file."""

# Dummy generic secret for the scanner. This is not a credential for any service.
api_key = "SCRUM95_SYNTHETIC_59c47e1a8b3f6d20e5a9c4b7d1e3f680"


def unsafe_probe(untrusted):
    return eval(untrusted)
