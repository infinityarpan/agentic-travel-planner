import logging


_configured = False


def configure_logging():
    global _configured
    if _configured:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    _configured = True


def get_logger(name):
    configure_logging()
    return logging.getLogger(name)
