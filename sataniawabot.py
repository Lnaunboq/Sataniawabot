"""Point d’entrée du bot."""
import logging
from setproctitle import setproctitle

if __package__:
    from .bot import SataniawaBot
    from .config import load_config
else:
    from bot import SataniawaBot
    from config import load_config


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    setproctitle("SataniawaBot")
    SataniawaBot(config).run(config.token)


if __name__ == "__main__":
    main()
