from utils.logger import setup_logger
from config import load_config


def main():
    logger = setup_logger()

    config = load_config()

    logger.info("=" * 60)
    logger.info("Khabar Bila Hudood Automation Started")
    logger.info("=" * 60)

    logger.info(f"Language: {config['project']['language']}")
    logger.info(f"Model: {config['ai']['model']}")
    logger.info(f"Video Resolution: {config['video']['resolution']}")

    logger.info("System initialized successfully.")


if __name__ == "__main__":
    main()
