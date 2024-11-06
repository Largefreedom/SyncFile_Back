import  logging
import constant
import colorlog

from colorama import Fore, Style

# Define colors for each log level
LOG_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        # Apply color based on the log level
        log_color = LOG_COLORS.get(record.levelno, Fore.WHITE)
        formatted_msg = super().format(record)

        # Format to include thread name and apply color
        return f"{log_color}[{record.threadName}] {formatted_msg}{Style.RESET_ALL}"




class Logger:
    def __init__(self):
    # Create handlers
        file_handler = logging.FileHandler(constant.LOG_SAVE_PATH)
        console_handler = logging.StreamHandler()
        # Set levels for the handlers
        file_handler.setLevel(logging.INFO)
        # Create a colorized formatter
        # console_formatter = colorlog.ColoredFormatter(
        #     "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        #     datefmt='%Y-%m-%d %H:%M:%S',
        #     log_colors={
        #         'DEBUG': 'cyan',
        #         'INFO': 'green',
        #         'WARNING': 'yellow',
        #         'ERROR': 'red',
        #         'CRITICAL': 'bold_red',
        #     }
        # )

        console_formatter = ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s-[%(threadName)s]- %(levelname)s - %(message)s')
        # Attach formatters to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(console_formatter)
        # Get a logger and attach handlers
        self.logger = logging.getLogger('my_app')
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        # not pass up to root logger,ensure not result duplicate output

    def info(self,msg):
        self.logger.info(msg)

    def error(self,msg):
        self.logger.error(msg)

    def debug(self,msg):
        self.logger.debug(msg)


logger = Logger()