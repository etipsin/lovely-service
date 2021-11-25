import logging
import socket
from typing import Union

from aiologstash import create_tcp_handler


class LogstashConnectionError(Exception):
    """Logstash Connection Error."""


class CustomLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None):
        extra = {"extras": extra}
        super(CustomLogger, self)._log(level, msg, args, exc_info, extra)


class ELKAsync:
    """Async Logstash/stderr logger."""

    tcp_handler = None
    logger = None

    def __init__(
        self,
        service_name: str,
        host: str = None,
        port: int = None,
        level: Union[int, str] = "INFO",
        logger_name: str = "nlab.elk",
        enable: bool = True,
    ):
        """
        Async Logstash/stderr logger.

        :param host: Logstash host.
        :param port: Logstash port.
        :param level: log level. Can be both int and str.
        :param service_name: service name.
        :param logger_name: logger name.
        :param enable: enable Logstash logger.
        """

        self.service_name = service_name
        self.host = host
        self.port = port
        self.level = level
        self.logger_name = logger_name
        self.enable_logstash = enable

        if not self.service_name:
            raise RuntimeWarning("Service name empty.")

        if not self.logger_name:
            raise RuntimeWarning("Logger name empty.")

    async def setup(self, _=None):
        """Aiohttp setup."""
        await self.connection_open()

        yield

        await self.connection_close()

    async def connection_open(self):
        """Setup logger and create handlers."""
        logging.setLoggerClass(CustomLogger)
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.level)

        # No need for duplicate messages
        logger.propagate = False

        logger.handlers = []

        stream = logging.StreamHandler()
        stream.setFormatter(
            logging.Formatter(
                fmt="%(asctime)-30s %(levelname)-10s %(message)s %(extras)s",
                datefmt="%Y.%m.%d %H:%M:%S",
            )
        )
        logger.addHandler(stream)

        logger.info(msg=f"Enabled stderr logger.")

        self.tcp_handler = None

        if self.enable_logstash:
            try:
                self.tcp_handler = await create_tcp_handler(
                    host=self.host,
                    port=self.port,
                    extra=dict(service_name=f"nlab.{self.service_name}"),
                )

                logger.info(
                    msg=f"Established connection to Logstash.",
                    extra={
                        "host": self.host,
                        "port": self.port,
                    },
                )
            except socket.gaierror:
                raise LogstashConnectionError(
                    "Logstash connection error. Check your config."
                ) from None

            logger.addHandler(self.tcp_handler)

        self.logger = logger

    async def connection_close(self):
        """Close connection to Logstash."""
        if self.tcp_handler:
            self.tcp_handler.close()
            await self.tcp_handler.wait_closed()

            self.logger.info(
                msg=f"Closed connection to Logstash.",
                extra={
                    "host": self.host,
                    "port": self.port,
                },
            )

    async def debug(self, msg, extra=None):
        if self.logger:
            self.logger.debug(msg=msg, extra=extra)

    async def info(self, msg, extra=None):
        if self.logger:
            self.logger.info(msg=msg, extra=extra)

    async def warning(self, msg, extra=None):
        if self.logger:
            self.logger.warning(msg=msg, extra=extra)

    async def error(self, msg, extra=None):
        if self.logger:
            self.logger.error(msg=msg, extra=extra)

    async def exception(self, msg, extra=None):
        if self.logger:
            self.logger.exception(msg=msg, extra=extra)

    async def critical(self, msg, extra=None):
        if self.logger:
            self.logger.critical(msg=msg, extra=extra)
