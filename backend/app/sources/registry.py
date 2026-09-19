from app.sources.autoru import AutoRuAdapter
from app.sources.avito import AvitoAdapter
from app.sources.drom import DromAdapter

adapters = {
    "autoru": AutoRuAdapter(),
    "avito": AvitoAdapter(),
    "drom": DromAdapter(),
}
