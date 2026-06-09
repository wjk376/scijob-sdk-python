import logging

logger = logging.getLogger("SciJob")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt="[%(name)s] %(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ),
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
