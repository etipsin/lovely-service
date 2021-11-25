import asyncpgsa
import orjson
from asyncpg.pool import Pool
from sqlalchemy.dialects import postgresql
from abc import ABC, abstractmethod
from typing import List, Optional


class AbstractStorage(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_dialect(self):
        pass

    async def setup(self, _=None):
        await self.connection_open()

        yield

        await self.connection_close()

    @abstractmethod
    async def connection_open(self):
        pass

    @abstractmethod
    async def connection_close(self):
        pass

    @abstractmethod
    async def fetch(self, query) -> list:
        pass

    @abstractmethod
    async def fetchrow(self, query) -> dict:
        pass


class AsyncpgsaStorage(AbstractStorage):
    connection: Optional[Pool]
    transaction: Optional
    transaction_connection: Optional

    def __init__(
        self,
        dsn: str = None,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        min_size: int = 10,
        max_size: int = 10,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
        logger=None,
    ):
        """
        Class which provides a wrapper around asyncpgsa package.

        :param dsn: Postgres dsn.
        :param host: Postgres host.
        :param port: Postgres port.
        :param database: Postgres database.
        :param user: Postgres user.
        :param password: Postgres password.
        :param min_size: Minimum number of connections in the pool.
        :param max_size: Maximum number of connections in the pool.
        :param max_queries: Number of queries after which a connection
         is closed and replaced with a new one.
        :param max_inactive_connection_lifetime: Number of seconds after which
         inactive connections in the pool will be closed.
          Pass 0 to turn this off.
        :param logger: Logger object.
        """
        super().__init__()

        self.connection = None

        self.dsn = dsn
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = int(min_size)
        self.max_size = int(max_size)
        self.max_queries = int(max_queries)
        self.max_inactive_connection_lifetime = float(max_inactive_connection_lifetime)

        self.logger = logger

        if not self.dsn and not (
            self.host and self.port and self.database and self.user and self.password
        ):
            raise RuntimeError("Postgres connections settings are not filled.")

    def get_dialect(self):
        """Get currently used SQLAlchemy dialect."""
        return postgresql

    async def connection_open(self):
        """Open connection to PostgreSQL."""
        if self.connection:
            await self.connection_close()

            raise RuntimeWarning(
                "Tried to open a new connection while a previous connection wasn't closed."
            )

        self.connection = await asyncpgsa.create_pool(
            dsn=self.dsn,
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            min_size=self.min_size,
            max_size=self.max_size,
            max_queries=self.max_queries,
            max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
            init=self.connection_init,
            # connection_class=SAConnection,
        )

        if self.logger:
            if self.dsn:
                extra = {"dsn": self.dsn}
            else:
                extra = {
                    "host": self.host,
                    "port": self.port,
                    "database": self.database,
                    "user": self.user,
                }

            await self.logger.info(
                msg=f"Established connection to PostgreSQL.",
                extra={
                    **extra,
                    "min_size": self.min_size,
                    "max_size": self.max_size,
                    "max_queries": self.max_queries,
                    "max_inactive_connection_lifetime": self.max_inactive_connection_lifetime,
                },
            )

    async def connection_close(self):
        """Close connection to PostgreSQL."""
        if not self.connection:
            raise RuntimeWarning(
                "Tried to close a connection without first opening it."
            )

        await self.connection.close()

        self.connection = None

        if self.logger:
            await self.logger.info(
                msg=f"Closed connection to PostgreSQL.",
                extra={
                    "dsn": self.dsn,
                    "host": self.host,
                    "port": self.port,
                    "database": self.database,
                    "user": self.user,
                },
            )

    @staticmethod
    async def connection_init(connection) -> None:
        """Modify PostgreSQL connection."""
        # Decode jsonb on arrival
        await connection.set_type_codec(
            "jsonb",
            encoder=str,
            decoder=orjson.loads,
            schema="pg_catalog",
        )

    async def log_query(self, query) -> None:
        """Log query."""
        if self.logger:
            try:
                q, p = asyncpgsa.compile_query(query)

                for i in range(len(p), 0, -1):
                    q = q.replace(f"${i}", str(p[i - 1]))

                q = q.replace("\n", " ")

                table = q.split('"')[1]
                query = q
            except:
                table = None

            await self.logger.info(
                msg="Executing query on PostgreSQL",
                extra={
                    "type": "DatabaseQuery",
                    "table": table,
                    "query": query,
                },
            )

    async def fetch(self, query, connection=None) -> list:
        """Fetch several rows."""
        await self.log_query(query)

        # If it is a transaction
        if connection:
            results = await connection.fetch(query)
        else:
            async with self.connection.acquire() as conn:
                results = await conn.fetch(query)

        return [dict(row) for row in results] if results else []

    async def fetchrow(self, query, connection=None) -> dict:
        """Fetch a single row."""
        await self.log_query(query)

        # If it is a transaction
        if connection:
            results = await connection.fetchrow(query)
        else:
            async with self.connection.acquire() as conn:
                results = await conn.fetchrow(query)

        return dict(results) if results else {}

    async def fetchfulljoin(self, query, connection=None) -> List[List[dict]]:
        """Fetch several rows and transform the results."""
        await self.log_query(query)

        # If it is a transaction
        if connection:
            results = await connection.fetch(query)
        else:
            async with self.connection.acquire() as conn:
                results = await conn.fetch(query)

        processed_results = []
        for result in results:
            temp = [{}]
            for key, value in result.items():
                if key in temp[-1]:
                    temp.append({})

                temp[-1][key] = value

            processed_results.append(temp)

        return processed_results
