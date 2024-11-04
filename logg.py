import  logging
import constant
import colorlog
class Logger:
    def __init__(self):
    # Create handlers
        file_handler = logging.FileHandler(constant.LOG_SAVE_PATH)
        console_handler = logging.StreamHandler()
        # Set levels for the handlers
        file_handler.setLevel(logging.ERROR)
        console_handler.setLevel(logging.DEBUG)
        # Create a colorized formatter
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )

        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Attach formatters to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(console_formatter)
        # Get a logger and attach handlers

        self.logger = logging.getLogger('my_app')
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        # not pass up to root logger,ensure not result duplicate output



    def info(self,msg):
        self.logger.info(msg)

    def error(self,msg):
        self.logger.error(msg)

    def debug(self,msg):
        self.logger.debug(msg)


