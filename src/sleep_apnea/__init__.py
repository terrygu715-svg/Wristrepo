"""Sleep apnea night-level classification package (scaffold, T03).

No models are implemented in T03. Subpackages below are reserved stubs so
later tickets have separate file ownership (T20/T21/T22 features,
T24/T25 evaluation, T26 artifacts); each stub documents its owning ticket.
"""

__version__ = "0.1.0"

# Canonical placeholder class order. Boundaries are UNVERIFIED (P05/E02):
# exact AHI cut points and inclusivity are frozen only at T12.
CLASS_ORDER = ("normal", "mild", "moderate", "severe")
N_CLASSES = 4
