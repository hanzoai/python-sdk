# Namespace package - see PEP 420
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
