import  logging
import constant
import os
import logging
import logging.handlers
import gzip
import shutil
from datetime import datetime


from colorama import Fore, Style

# Define colors for each log level
LOG_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA
}



class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    # compress log size clas
    def doRollover(self):
        # Call the parent class's method to rotate the file
        super().doRollover()
        # Compress the old log file
        if self.backupCount > 0:
            old_log_filename = f"{self.baseFilename}.{self.backupCount}"
            compressed_log_filename = f"{datetime.now().strftime('%Y_%m_%d')}_{old_log_filename}.gz"
            # Compress the old log file
            with open(old_log_filename, 'rb') as f_in:
                with gzip.open(compressed_log_filename, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # Remove the uncompressed log file
            os.remove(old_log_filename)



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
        console_formatter = ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        # # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s-[%(threadName)s]- %(levelname)s - %(message)s')
        # # Attach formatters to handlers
        # file_handler.setFormatter(formatter)
        console_handler.setFormatter(console_formatter)
        file_handler = CompressedRotatingFileHandler(filename=constant.LOG_SAVE_PATH,
                                                     maxBytes=constant.LOG_MAX_SIZE,
                                                     backupCount=constant.LOG_BACK_COUNT)
        file_handler.setFormatter(formatter)
        # Get a logger and attach handlers
        self.logger = logging.getLogger()
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
