from .gul import GulService
from .ladok import LadokService
from .account import AccountService


SERVICE_LIST = [
    GulService,
    LadokService,
    AccountService,
]

SERVICE_DICT = {
    cls.NAME: cls
    for cls in SERVICE_LIST
}
