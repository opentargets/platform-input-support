import logging
import logging.config


class Logger:
    @classmethod
    def init(cls, config: dict | None):
        default_config = {
            'version': 1,
            'root': {'level': 'DEBUG', 'handlers': ['console', 'file']},
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'brief',
                    'stream': 'ext://sys.stdout',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'precise',
                    'filename': 'output.log',
                    'mode': 'a',
                },
            },
            'formatters': {
                'brief': {
                    'format': '%(asctime)s - %(name)-12s: %(levelname)-4s - %(message)s',
                    'datefmt': '%H:%M:%S',
                },
                'precise': {
                    'format': '%(asctime)s - %(name)-s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
            },
        }

        for key, value in config.items():
            if key in default_config:
                if isinstance(default_config[key], dict) and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

        logging.config.dictConfig(default_config)

    @classmethod
    def get(cls, name: str | None = None) -> logging.Logger:
        return logging.getLogger(name)

    @classmethod
    def get_level_name(cls) -> str:
        return logging.getLevelName(logging.getLogger().getEffectiveLevel())
