import json
from typing import Annotated, Any, Union

import pytest
from pydantic_core import PydanticCustomError, PydanticSerializationError, Url

from pydantic import (
    AfterValidator,
    AmqpDsn,
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ClickHouseDsn,
    CockroachDsn,
    Field,
    FileUrl,
    FtpUrl,
    HttpUrl,
    KafkaDsn,
    MariaDBDsn,
    MongoDsn,
    MySQLDsn,
    NameEmail,
    NatsDsn,
    PostgresDsn,
    RedisDsn,
    SnowflakeDsn,
    Strict,
    TypeAdapter,
    UrlConstraints,
    ValidationError,
    WebsocketUrl,
)
from pydantic.networks import import_email_validator, validate_email

try:
    import email_validator
except ImportError:
    email_validator = None


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'http://test',
        'http://localhost',
        'https://example.org/whatever/next/',
        'postgres://user:pass@localhost:5432/app',
        'postgres://just-user@localhost:5432/app',
        'postgresql+asyncpg://user:pass@localhost:5432/app',
        'postgresql+pg8000://user:pass@localhost:5432/app',
        'postgresql+psycopg://postgres:postgres@localhost:5432/hatch',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/hatch',
        'postgresql+psycopg2cffi://user:pass@localhost:5432/app',
        'postgresql+py-postgresql://user:pass@localhost:5432/app',
        'postgresql+pygresql://user:pass@localhost:5432/app',
        'mysql://user:pass@localhost:3306/app',
        'mysql+mysqlconnector://user:pass@localhost:3306/app',
        'mysql+aiomysql://user:pass@localhost:3306/app',
        'mysql+asyncmy://user:pass@localhost:3306/app',
        'mysql+mysqldb://user:pass@localhost:3306/app',
        'mysql+pymysql://user:pass@localhost:3306/app?charset=utf8mb4',
        'mysql+cymysql://user:pass@localhost:3306/app',
        'mysql+pyodbc://user:pass@localhost:3306/app',
        'mariadb://user:pass@localhost:3306/app',
        'mariadb+mariadbconnector://user:pass@localhost:3306/app',
        'mariadb+pymysql://user:pass@localhost:3306/app',
        'snowflake://user:pass@myorganization-myaccount',
        'snowflake://user:pass@myorganization-myaccount/testdb/public?warehouse=testwh&role=myrole',
        'foo-bar://example.org',
        'foo.bar://example.org',
        'foo0bar://example.org',
        'https://example.org',
        'http://localhost',
        'http://localhost/',
        'http://localhost:8000',
        'http://localhost:8000/',
        'https://foo_bar.example.com/',
        'ftp://example.org',
        'ftps://example.org',
        'http://example.co.jp',
        'http://www.example.com/a%C2%B1b',
        'http://www.example.com/~username/',
        'http://info.example.com?fred',
        'http://info.example.com/?fred',
        'http://xn--mgbh0fb.xn--kgbechtv/',
        'http://example.com/blue/red%3Fand+green',
        'http://www.example.com/?array%5Bkey%5D=value',
        'http://xn--rsum-bpad.example.org/',
        'http://123.45.67.8/',
        'http://123.45.67.8:8329/',
        'http://[2001:db8::ff00:42]:8329',
        'http://[2001::1]:8329',
        'http://[2001:db8::1]/',
        'http://www.example.com:8000/foo',
        'http://www.cwi.nl:80/%7Eguido/Python.html',
        'https://www.python.org/путь',
        'http://андрей@example.com',
        # AnyUrl('https://example.com', scheme='https', host='example.com'),
        'https://exam_ple.com/',
        'http://twitter.com/@handle/',
        'http://11.11.11.11.example.com/action',
        'http://abc.11.11.11.11.example.com/action',
        'http://example#',
        'http://example/#',
        'http://example/#fragment',
        'http://example/?#',
        'http://example.org/path#',
        'http://example.org/path#fragment',
        'http://example.org/path?query#',
        'http://example.org/path?query#fragment',
    ],
)
def test_any_url_success(value):
    class Model(BaseModel):
        v: AnyUrl

    assert Model(v=value).v, value


@pytest.mark.parametrize(
    'value,err_type,err_msg',
    [
        ('http:///', 'url_parsing', 'Input should be a valid URL, empty host'),
        ('http://??', 'url_parsing', 'Input should be a valid URL, empty host'),
        pytest.param(
            'https://example.org more',
            'url_parsing',
            'Input should be a valid URL, invalid international domain name',
            marks=pytest.mark.skip(
                reason='Skipping until pydantic-core version with url validation updates is available'
            ),
        ),
        ('$https://example.org', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('../icons/logo.gif', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('abc', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('..', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('/', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('+http://example.com/', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('ht*tp://example.com/', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        (' ', 'url_parsing', 'Input should be a valid URL, relative URL without a base'),
        ('', 'url_parsing', 'Input should be a valid URL, input is empty'),
        (None, 'url_type', 'URL input should be a string or URL'),
        (
            'http://2001:db8::ff00:42:8329',
            'url_parsing',
            'Input should be a valid URL, invalid port number',
        ),
        ('http://[192.168.1.1]:8329', 'url_parsing', 'Input should be a valid URL, invalid IPv6 address'),
        ('http://example.com:99999', 'url_parsing', 'Input should be a valid URL, invalid port number'),
    ],
)
def test_any_url_invalid(value, err_type, err_msg):
    class Model(BaseModel):
        v: AnyUrl

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert len(exc_info.value.errors(include_url=False)) == 1, exc_info.value.errors(include_url=False)
    error = exc_info.value.errors(include_url=False)[0]
    # debug(error)
    assert {'type': error['type'], 'msg': error['msg']} == {'type': err_type, 'msg': err_msg}


def validate_url(s):
    class Model(BaseModel):
        v: AnyUrl

    return Model(v=s).v


def test_any_url_parts():
    url = validate_url('http://example.org')
    assert str(url) == 'http://example.org/'
    assert repr(url) == "AnyUrl('http://example.org/')"
    assert url.scheme == 'http'
    assert url.host == 'example.org'
    assert url.port == 80


def test_url_repr():
    url = validate_url('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit')
    assert str(url) == 'http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit'
    assert repr(url) == "AnyUrl('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit')"
    assert url.scheme == 'http'
    assert url.username == 'user'
    assert url.password == 'password'
    assert url.host == 'example.org'
    assert url.port == 1234
    assert url.path == '/the/path/'
    assert url.query == 'query=here'
    assert url.fragment == 'fragment=is;this=bit'


def test_ipv4_port():
    url = validate_url('ftp://123.45.67.8:8329/')
    assert url.scheme == 'ftp'
    assert url.host == '123.45.67.8'
    assert url.port == 8329
    assert url.username is None
    assert url.password is None


def test_ipv4_no_port():
    url = validate_url('ftp://123.45.67.8')
    assert url.scheme == 'ftp'
    assert url.host == '123.45.67.8'
    assert url.port == 21
    assert url.username is None
    assert url.password is None


def test_ipv6_port():
    url = validate_url('wss://[2001:db8::ff00:42]:8329')
    assert url.scheme == 'wss'
    assert url.host == '[2001:db8::ff00:42]'
    assert url.port == 8329


def test_int_domain():
    url = validate_url('https://£££.org')
    assert url.host == 'xn--9aaa.org'
    assert str(url) == 'https://xn--9aaa.org/'


def test_co_uk():
    url = validate_url('http://example.co.uk')
    assert str(url) == 'http://example.co.uk/'
    assert url.scheme == 'http'
    assert url.host == 'example.co.uk'


def test_user_no_password():
    url = validate_url('http://user:@example.org')
    assert url.username == 'user'
    assert url.password is None
    assert url.host == 'example.org'


def test_user_info_no_user():
    url = validate_url('http://:password@example.org')
    assert url.username is None
    assert url.password == 'password'
    assert url.host == 'example.org'


def test_at_in_path():
    url = validate_url('https://twitter.com/@handle')
    assert url.scheme == 'https'
    assert url.host == 'twitter.com'
    assert url.username is None
    assert url.password is None
    assert url.path == '/@handle'


def test_fragment_without_query():
    url = validate_url('https://docs.pydantic.dev/usage/types/#constrained-types')
    assert url.scheme == 'https'
    assert url.host == 'docs.pydantic.dev'
    assert url.path == '/usage/types/'
    assert url.query is None
    assert url.fragment == 'constrained-types'


@pytest.mark.parametrize(
    'value,expected',
    [
        ('http://example.org', 'http://example.org/'),
        ('http://example.org/foobar', 'http://example.org/foobar'),
        ('http://example.org.', 'http://example.org./'),
        ('http://example.org./foobar', 'http://example.org./foobar'),
        ('HTTP://EXAMPLE.ORG', 'http://example.org/'),
        ('https://example.org', 'https://example.org/'),
        ('https://example.org?a=1&b=2', 'https://example.org/?a=1&b=2'),
        ('https://example.org#a=3;b=3', 'https://example.org/#a=3;b=3'),
        ('https://foo_bar.example.com/', 'https://foo_bar.example.com/'),
        ('https://exam_ple.com/', 'https://exam_ple.com/'),
        ('https://example.xn--p1ai', 'https://example.xn--p1ai/'),
        ('https://example.xn--vermgensberatung-pwb', 'https://example.xn--vermgensberatung-pwb/'),
        ('https://example.xn--zfr164b', 'https://example.xn--zfr164b/'),
    ],
)
def test_http_url_success(value, expected):
    class Model(BaseModel):
        v: HttpUrl

    assert str(Model(v=value).v) == expected


def test_nullable_http_url():
    class Model(BaseModel):
        v: Union[HttpUrl, None]

    assert Model(v=None).v is None
    assert str(Model(v='http://example.org').v) == 'http://example.org/'


@pytest.mark.parametrize(
    'value,err_type,err_msg',
    [
        (
            'ftp://example.com/',
            'url_scheme',
            "URL scheme should be 'http' or 'https'",
        ),
        (
            'x' * 2084,
            'url_too_long',
            'URL should have at most 2083 characters',
        ),
    ],
)
def test_http_url_invalid(value, err_type, err_msg):
    class Model(BaseModel):
        v: HttpUrl

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert len(exc_info.value.errors(include_url=False)) == 1, exc_info.value.errors(include_url=False)
    error = exc_info.value.errors(include_url=False)[0]
    assert {'type': error['type'], 'msg': error['msg']} == {'type': err_type, 'msg': err_msg}


@pytest.mark.parametrize(
    'input,output',
    [
        ('  https://www.example.com \n', 'https://www.example.com/'),
        (b'https://www.example.com', 'https://www.example.com/'),
        # https://www.xudongz.com/blog/2017/idn-phishing/ accepted but converted
        ('https://www.аррӏе.com/', 'https://www.xn--80ak6aa92e.com/'),
        ('https://exampl£e.org', 'https://xn--example-gia.org/'),
        ('https://example.珠宝', 'https://example.xn--pbt977c/'),
        ('https://example.vermögensberatung', 'https://example.xn--vermgensberatung-pwb/'),
        ('https://example.рф', 'https://example.xn--p1ai/'),
        ('https://exampl£e.珠宝', 'https://xn--example-gia.xn--pbt977c/'),
    ],
)
def test_coerce_url(input, output):
    class Model(BaseModel):
        v: HttpUrl

    assert str(Model(v=input).v) == output


@pytest.mark.parametrize(
    'value,expected',
    [
        ('file:///foo/bar', 'file:///foo/bar'),
        ('file://localhost/foo/bar', 'file:///foo/bar'),
        ('file:////localhost/foo/bar', 'file:///localhost/foo/bar'),
    ],
)
def test_file_url_success(value, expected):
    class Model(BaseModel):
        v: FileUrl

    assert str(Model(v=value).v) == expected


@pytest.mark.parametrize(
    'url,expected_port, expected_str',
    [
        ('https://www.example.com/', 443, 'https://www.example.com/'),
        ('https://www.example.com:443/', 443, 'https://www.example.com/'),
        ('https://www.example.com:8089/', 8089, 'https://www.example.com:8089/'),
        ('http://www.example.com/', 80, 'http://www.example.com/'),
        ('http://www.example.com:80/', 80, 'http://www.example.com/'),
        ('http://www.example.com:8080/', 8080, 'http://www.example.com:8080/'),
    ],
)
def test_http_urls_default_port(url, expected_port, expected_str):
    class Model(BaseModel):
        v: HttpUrl

    m = Model(v=url)
    assert m.v.port == expected_port
    assert str(m.v) == expected_str


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ws://example.com', 'ws://example.com/'),
        ('wss://example.com', 'wss://example.com/'),
        ('wss://ws.example.com/', 'wss://ws.example.com/'),
        ('ws://ws.example.com/', 'ws://ws.example.com/'),
        ('ws://example.com:8080', 'ws://example.com:8080/'),
        ('ws://example.com/path', 'ws://example.com/path'),
        ('wss://example.com:4433', 'wss://example.com:4433/'),
        ('wss://example.com/path', 'wss://example.com/path'),
    ],
)
def test_websocket_url_success(value, expected):
    class Schema(BaseModel):
        ws: WebsocketUrl

    assert Schema(ws=value).ws.unicode_string() == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ws://example.com', 80),
        ('wss://example.com', 443),
        ('wss://ws.example.com/', 443),
        ('ws://ws.example.com/', 80),
        ('ws://example.com:8080', 8080),
        ('ws://example.com:9999/path', 9999),
        ('wss://example.com:4433', 4433),
        ('wss://example.com/path', 443),
    ],
)
def test_websocket_url_port_success(value, expected):
    class Schema(BaseModel):
        ws: WebsocketUrl

    assert Schema(ws=value).ws.port == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ws://example.com', '/'),
        ('wss://example.com', '/'),
        ('wss://ws.example.com/', '/'),
        ('ws://ws.example.com/', '/'),
        ('ws://example.com:8080', '/'),
        ('ws://example.com:9999/path', '/path'),
        ('wss://example.com:4433', '/'),
        ('wss://example.com/path/to/ws', '/path/to/ws'),
    ],
)
def test_websocket_url_path_success(value, expected):
    class Schema(BaseModel):
        ws: WebsocketUrl

    assert Schema(ws=value).ws.path == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ftp://example.com', 'ftp://example.com/'),
        ('ftp://example.com/path/to/ftp', 'ftp://example.com/path/to/ftp'),
        ('ftp://example.com:21', 'ftp://example.com/'),
        ('ftp://example.com:21/path/to/ftp', 'ftp://example.com/path/to/ftp'),
        ('ftp://example.com', 'ftp://example.com/'),
        ('ftp://example.com/path/to/ftp', 'ftp://example.com/path/to/ftp'),
        ('ftp://example.com:990', 'ftp://example.com:990/'),
        ('ftp://example.com:990/path/to/ftp', 'ftp://example.com:990/path/to/ftp'),
    ],
)
def test_ftp_url_success(value, expected):
    class Schema(BaseModel):
        ftp: FtpUrl

    assert Schema(ftp=value).ftp.unicode_string() == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ftp://example.com', 21),
        ('ftp://example.com/path/to/ftp', 21),
        ('ftp://example.com:21', 21),
        ('ftp://exaMplФ.com:221/path/to/ftp', 221),
        ('ftp://example.com:144', 144),
        ('ftp://example.com:990/path/to/ftp', 990),
    ],
)
def test_ftp_url_port_success(value, expected):
    class Schema(BaseModel):
        ftp: FtpUrl

    assert Schema(ftp=value).ftp.port == expected


@pytest.mark.parametrize(
    'dsn',
    [
        'postgres://user:pass@localhost:5432/app',
        'postgresql://user:pass@localhost:5432/app',
        'postgresql+asyncpg://user:pass@localhost:5432/app',
        'postgres://user:pass@host1.db.net,host2.db.net:6432/app',
        'postgres://user:pass@%2Fvar%2Flib%2Fpostgresql/dbname',
    ],
)
def test_postgres_dsns(dsn):
    class Model(BaseModel):
        a: PostgresDsn

    assert str(Model(a=dsn).a) == dsn


@pytest.mark.parametrize(
    'dsn',
    [
        'mysql://user:pass@localhost:3306/app',
        'mysql+mysqlconnector://user:pass@localhost:3306/app',
        'mysql+aiomysql://user:pass@localhost:3306/app',
        'mysql+asyncmy://user:pass@localhost:3306/app',
        'mysql+mysqldb://user:pass@localhost:3306/app',
        'mysql+pymysql://user:pass@localhost:3306/app?charset=utf8mb4',
        'mysql+cymysql://user:pass@localhost:3306/app',
        'mysql+pyodbc://user:pass@localhost:3306/app',
    ],
)
def test_mysql_dsns(dsn):
    class Model(BaseModel):
        a: MySQLDsn

    assert str(Model(a=dsn).a) == dsn


@pytest.mark.parametrize(
    'dsn',
    [
        'mariadb://user:pass@localhost:3306/app',
        'mariadb+mariadbconnector://user:pass@localhost:3306/app',
        'mariadb+pymysql://user:pass@localhost:3306/app',
    ],
)
def test_mariadb_dsns(dsn):
    class Model(BaseModel):
        a: MariaDBDsn

    assert str(Model(a=dsn).a) == dsn


@pytest.mark.parametrize(
    'dsn',
    [
        'clickhouse+native://user:pass@localhost:9000/app',
        'clickhouse+asynch://user:pass@localhost:9000/app',
        'clickhouse+http://user:pass@localhost:9000/app',
        'clickhouse://user:pass@localhost:9000/app',
        'clickhouses://user:pass@localhost:9000/app',
        'clickhousedb://user:pass@localhost:9000/app',
    ],
)
def test_clickhouse_dsns(dsn):
    class Model(BaseModel):
        a: ClickHouseDsn

    assert str(Model(a=dsn).a) == dsn


@pytest.mark.parametrize(
    'dsn',
    [
        'snowflake://user:pass@myorganization-myaccount',
        'snowflake://user:pass@myorganization-myaccount/testdb/public?warehouse=testwh&role=myrole',
    ],
)
def test_snowflake_dsns(dsn):
    class Model(BaseModel):
        a: SnowflakeDsn

    assert str(Model(a=dsn).a) == dsn


@pytest.mark.parametrize(
    'dsn,error_message',
    (
        (
            'postgres://user:pass@host1.db.net:4321,/foo/bar:5432/app',
            {
                'type': 'url_parsing',
                'loc': ('a',),
                'msg': 'Input should be a valid URL, empty host',
                'input': 'postgres://user:pass@host1.db.net:4321,/foo/bar:5432/app',
            },
        ),
        (
            'postgres://user:pass@host1.db.net,/app',
            {
                'type': 'url_parsing',
                'loc': ('a',),
                'msg': 'Input should be a valid URL, empty host',
                'input': 'postgres://user:pass@host1.db.net,/app',
            },
        ),
        (
            'postgres://user:pass@/foo/bar:5432,host1.db.net:4321/app',
            {
                'type': 'url_parsing',
                'loc': ('a',),
                'msg': 'Input should be a valid URL, empty host',
                'input': 'postgres://user:pass@/foo/bar:5432,host1.db.net:4321/app',
            },
        ),
        (
            'postgres://user@/foo/bar:5432/app',
            {
                'type': 'url_parsing',
                'loc': ('a',),
                'msg': 'Input should be a valid URL, empty host',
                'input': 'postgres://user@/foo/bar:5432/app',
            },
        ),
        (
            'http://example.org',
            {
                'type': 'url_scheme',
                'loc': ('a',),
                'msg': (
                    "URL scheme should be 'postgres', 'postgresql', 'postgresql+asyncpg', 'postgresql+pg8000', "
                    "'postgresql+psycopg', 'postgresql+psycopg2', 'postgresql+psycopg2cffi', "
                    "'postgresql+py-postgresql' or 'postgresql+pygresql'"
                ),
                'input': 'http://example.org',
            },
        ),
    ),
)
def test_postgres_dsns_validation_error(dsn, error_message):
    class Model(BaseModel):
        a: PostgresDsn

    with pytest.raises(ValidationError) as exc_info:
        Model(a=dsn)
    error = exc_info.value.errors(include_url=False)[0]
    error.pop('ctx', None)
    assert error == error_message


def test_multihost_postgres_dsns():
    class Model(BaseModel):
        a: PostgresDsn

    any_multihost_url = Model(a='postgres://user:pass@host1.db.net:4321,host2.db.net:6432/app').a
    assert str(any_multihost_url) == 'postgres://user:pass@host1.db.net:4321,host2.db.net:6432/app'
    assert any_multihost_url.scheme == 'postgres'
    assert any_multihost_url.path == '/app'
    # insert_assert(any_multihost_url.hosts())
    assert any_multihost_url.hosts() == [
        {'username': 'user', 'password': 'pass', 'host': 'host1.db.net', 'port': 4321},
        {'username': None, 'password': None, 'host': 'host2.db.net', 'port': 6432},
    ]

    any_multihost_url = Model(a='postgres://user:pass@host.db.net:4321/app').a
    assert any_multihost_url.scheme == 'postgres'
    assert str(any_multihost_url) == 'postgres://user:pass@host.db.net:4321/app'
    assert any_multihost_url.path == '/app'
    # insert_assert(any_multihost_url.hosts())
    assert any_multihost_url.hosts() == [{'username': 'user', 'password': 'pass', 'host': 'host.db.net', 'port': 4321}]


def test_cockroach_dsns():
    class Model(BaseModel):
        a: CockroachDsn

    assert str(Model(a='cockroachdb://user:pass@localhost:5432/app').a) == 'cockroachdb://user:pass@localhost:5432/app'
    assert (
        str(Model(a='cockroachdb+psycopg2://user:pass@localhost:5432/app').a)
        == 'cockroachdb+psycopg2://user:pass@localhost:5432/app'
    )
    assert (
        str(Model(a='cockroachdb+asyncpg://user:pass@localhost:5432/app').a)
        == 'cockroachdb+asyncpg://user:pass@localhost:5432/app'
    )

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'url_scheme'


def test_amqp_dsns():
    class Model(BaseModel):
        a: AmqpDsn

    m = Model(a='amqp://user:pass@localhost:1234/app')
    assert str(m.a) == 'amqp://user:pass@localhost:1234/app'
    assert m.a.username == 'user'
    assert m.a.password == 'pass'

    m = Model(a='amqps://user:pass@localhost:5432//')
    assert str(m.a) == 'amqps://user:pass@localhost:5432//'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'url_scheme'

    # Password is not required for AMQP protocol
    m = Model(a='amqp://localhost:1234/app')
    assert str(m.a) == 'amqp://localhost:1234/app'
    assert m.a.username is None
    assert m.a.password is None

    # Only schema is required for AMQP protocol.
    # https://www.rabbitmq.com/uri-spec.html
    m = Model(a='amqps://')
    assert m.a.scheme == 'amqps'
    assert m.a.host is None
    assert m.a.port is None
    assert m.a.path is None


def test_redis_dsns():
    class Model(BaseModel):
        a: RedisDsn

    m = Model(a='redis://user:pass@localhost:1234/app')
    assert str(m.a) == 'redis://user:pass@localhost:1234/app'
    assert m.a.username == 'user'
    assert m.a.password == 'pass'

    m = Model(a='rediss://user:pass@localhost:1234/app')
    assert str(m.a) == 'rediss://user:pass@localhost:1234/app'

    m = Model(a='rediss://:pass@localhost:1234')
    assert str(m.a) == 'rediss://:pass@localhost:1234/0'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'url_scheme'

    # Password is not required for Redis protocol
    m = Model(a='redis://localhost:1234/app')
    assert str(m.a) == 'redis://localhost:1234/app'
    assert m.a.username is None
    assert m.a.password is None

    # Only schema is required for Redis protocol. Otherwise it will be set to default
    # https://www.iana.org/assignments/uri-schemes/prov/redis
    m = Model(a='rediss://')
    assert m.a.scheme == 'rediss'
    assert m.a.host == 'localhost'
    assert m.a.port == 6379
    assert m.a.path == '/0'


def test_mongodb_dsns():
    class Model(BaseModel):
        a: MongoDsn

    # TODO: Need to unit tests about "Replica Set", "Sharded cluster" and other deployment modes of MongoDB
    m = Model(a='mongodb://user:pass@localhost:1234/app')
    assert str(m.a) == 'mongodb://user:pass@localhost:1234/app'
    # insert_assert(m.a.hosts())
    assert m.a.hosts() == [{'username': 'user', 'password': 'pass', 'host': 'localhost', 'port': 1234}]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'url_scheme'

    # Password is not required for MongoDB protocol
    m = Model(a='mongodb://localhost:1234/app')
    assert str(m.a) == 'mongodb://localhost:1234/app'
    # insert_assert(m.a.hosts())
    assert m.a.hosts() == [{'username': None, 'password': None, 'host': 'localhost', 'port': 1234}]

    # Only schema and host is required for MongoDB protocol
    m = Model(a='mongodb://localhost')
    assert m.a.scheme == 'mongodb'
    # insert_assert(m.a.hosts())
    assert m.a.hosts() == [{'username': None, 'password': None, 'host': 'localhost', 'port': 27017}]


@pytest.mark.parametrize(
    ('dsn', 'expected'),
    [
        ('mongodb://user:pass@localhost/app', 'mongodb://user:pass@localhost:27017/app'),
        pytest.param(
            'mongodb+srv://user:pass@localhost/app',
            'mongodb+srv://user:pass@localhost/app',
            marks=pytest.mark.xfail(
                reason=(
                    'This case is not supported. Check https://github.com/pydantic/pydantic/pull/7116 for more details.'
                )
            ),
        ),
    ],
)
def test_mongodsn_default_ports(dsn: str, expected: str):
    class Model(BaseModel):
        dsn: MongoDsn

    m = Model(dsn=dsn)
    assert str(m.dsn) == expected


def test_kafka_dsns():
    class Model(BaseModel):
        a: KafkaDsn

    m = Model(a='kafka://')
    assert m.a.scheme == 'kafka'
    assert m.a.host == 'localhost'
    assert m.a.port == 9092
    assert str(m.a) == 'kafka://localhost:9092'

    m = Model(a='kafka://kafka1')
    assert str(m.a) == 'kafka://kafka1:9092'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'url_scheme'

    m = Model(a='kafka://kafka3:9093')
    assert m.a.username is None
    assert m.a.password is None


@pytest.mark.parametrize(
    'dsn,result',
    [
        ('nats://user:pass@localhost:4222', 'nats://user:pass@localhost:4222'),
        ('tls://user@localhost', 'tls://user@localhost:4222'),
        ('ws://localhost:2355', 'ws://localhost:2355/'),
        ('tls://', 'tls://localhost:4222'),
        ('ws://:password@localhost:9999', 'ws://:password@localhost:9999/'),
    ],
)
def test_nats_dsns(dsn, result):
    class Model(BaseModel):
        dsn: NatsDsn

    assert str(Model(dsn=dsn).dsn) == result


def test_custom_schemes():
    class Model(BaseModel):
        v: Annotated[Url, UrlConstraints(allowed_schemes=['ws', 'wss']), Strict()]

    class Model2(BaseModel):
        v: Annotated[Url, UrlConstraints(host_required=False, allowed_schemes=['foo'])]

    assert str(Model(v='ws://example.org').v) == 'ws://example.org/'
    assert str(Model2(v='foo:///foo/bar').v) == 'foo:///foo/bar'

    with pytest.raises(ValidationError, match=r"URL scheme should be 'ws' or 'wss' \[type=url_scheme,"):
        Model(v='http://example.org')

    with pytest.raises(ValidationError, match='leading or trailing control or space character are ignored in URLs'):
        Model(v='ws://example.org  ')

    with pytest.raises(ValidationError, match=r'syntax rules, expected // \[type=url_syntax_violation,'):
        Model(v='ws:///foo/bar')


@pytest.mark.parametrize(
    'options',
    [
        # Ensures the hash is generated correctly when a field is null
        {'max_length': None},
        {'allowed_schemes': None},
        {'host_required': None},
        {'default_host': None},
        {'default_port': None},
        {'default_path': None},
    ],
)
def test_url_constraints_hash_equal(options):
    defaults = {
        'max_length': 1,
        'allowed_schemes': ['scheme'],
        'host_required': False,
        'default_host': 'host',
        'default_port': 0,
        'default_path': 'path',
    }
    options = {**defaults, **options}
    assert hash(UrlConstraints(**options)) == hash(UrlConstraints(**options))


@pytest.mark.parametrize(
    'changes',
    [
        {'max_length': 2},
        {'allowed_schemes': ['new-scheme']},
        {'host_required': True},
        {'default_host': 'new-host'},
        {'default_port': 1},
        {'default_path': 'new-path'},
        {'max_length': None},
        {'allowed_schemes': None},
        {'host_required': None},
        {'default_host': None},
        {'default_port': None},
        {'default_path': None},
    ],
)
def test_url_constraints_hash_inequal(changes):
    options = {
        'max_length': 1,
        'allowed_schemes': ['scheme'],
        'host_required': False,
        'default_host': 'host',
        'default_port': 0,
        'default_path': 'path',
    }
    assert hash(UrlConstraints(**options)) != hash(UrlConstraints(**{**options, **changes}))


def test_json():
    class Model(BaseModel):
        v: HttpUrl

    m = Model(v='http://foo@example.net')
    assert m.model_dump_json() == '{"v":"http://foo@example.net/"}'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize(
    'value,name,email',
    [
        ('foobar@example.com', 'foobar', 'foobar@example.com'),
        ('s@muelcolvin.com', 's', 's@muelcolvin.com'),
        ('Samuel Colvin <s@muelcolvin.com>', 'Samuel Colvin', 's@muelcolvin.com'),
        ('foobar <foobar@example.com>', 'foobar', 'foobar@example.com'),
        (' foo.bar@example.com', 'foo.bar', 'foo.bar@example.com'),
        ('foo.bar@example.com ', 'foo.bar', 'foo.bar@example.com'),
        ('foo BAR <foobar@example.com >', 'foo BAR', 'foobar@example.com'),
        ('FOO bar   <foobar@example.com> ', 'FOO bar', 'foobar@example.com'),
        (' Whatever <foobar@example.com>', 'Whatever', 'foobar@example.com'),
        ('Whatever < foobar@example.com>', 'Whatever', 'foobar@example.com'),
        ('Whatever <foobar@example.com >', 'Whatever', 'foobar@example.com'),
        ('Whatever < foobar@example.com >', 'Whatever', 'foobar@example.com'),
        ('<FOOBAR@example.com> ', 'FOOBAR', 'FOOBAR@example.com'),
        ('ñoñó@example.com', 'ñoñó', 'ñoñó@example.com'),
        ('我買@example.com', '我買', '我買@example.com'),
        ('甲斐黒川日本@example.com', '甲斐黒川日本', '甲斐黒川日本@example.com'),
        (
            'чебурашкаящик-с-апельсинами.рф@example.com',
            'чебурашкаящик-с-апельсинами.рф',
            'чебурашкаящик-с-апельсинами.рф@example.com',
        ),
        ('उदाहरण.परीक्ष@domain.with.idn.tld', 'उदाहरण.परीक्ष', 'उदाहरण.परीक्ष@domain.with.idn.tld'),
        ('foo.bar@example.com', 'foo.bar', 'foo.bar@example.com'),
        ('foo.bar@exam-ple.com ', 'foo.bar', 'foo.bar@exam-ple.com'),
        ('ιωάννης@εεττ.gr', 'ιωάννης', 'ιωάννης@εεττ.gr'),
        ('foobar@аррӏе.com', 'foobar', 'foobar@аррӏе.com'),
        ('foobar@xn--80ak6aa92e.com', 'foobar', 'foobar@аррӏе.com'),
        ('аррӏе@example.com', 'аррӏе', 'аррӏе@example.com'),
        ('xn--80ak6aa92e@example.com', 'xn--80ak6aa92e', 'xn--80ak6aa92e@example.com'),
        ('葉士豪@臺網中心.tw', '葉士豪', '葉士豪@臺網中心.tw'),
        ('"first.last" <first.last@example.com>', 'first.last', 'first.last@example.com'),
        ("Shaquille O'Neal <shaq@example.com>", "Shaquille O'Neal", 'shaq@example.com'),
    ],
)
def test_address_valid(value, name, email):
    assert validate_email(value) == (name, email)


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize(
    'value,reason',
    [
        ('@example.com', 'There must be something before the @-sign.'),
        ('f oo.bar@example.com', 'The email address contains invalid characters before the @-sign'),
        ('foobar', 'An email address must have an @-sign.'),
        ('foobar@localhost', 'The part after the @-sign is not valid. It should have a period.'),
        ('foobar@127.0.0.1', 'The part after the @-sign is not valid. It is not within a valid top-level domain.'),
        ('foo.bar@exam\nple.com ', None),
        ('foobar <foobar@example.com', None),
        ('foobar@.example.com', None),
        ('foobar@.com', None),
        ('foo bar@example.com', None),
        ('foo@bar@example.com', None),
        ('\n@example.com', None),
        ('\r@example.com', None),
        ('\f@example.com', None),
        (' @example.com', None),
        ('\u0020@example.com', None),
        ('\u001f@example.com', None),
        ('"@example.com', None),
        (',@example.com', None),
        ('foobar <foobar<@example.com>', None),
        ('foobar <foobar@example.com>>', None),
        ('foobar <<foobar<@example.com>', None),
        ('foobar <>', None),
        ('first.last <first.last@example.com>', None),
        pytest.param('foobar <' + 'a' * 4096 + '@example.com>', 'Length must not exceed 2048 characters', id='long'),
    ],
)
def test_address_invalid(value: str, reason: Union[str, None]):
    with pytest.raises(PydanticCustomError, match=f'value is not a valid email address: {reason or ""}'):
        validate_email(value)


def test_email_validator_not_installed(mocker):
    mocker.patch('pydantic.networks.email_validator', None)
    m = mocker.patch('pydantic.networks.import_email_validator', side_effect=ImportError)
    with pytest.raises(ImportError):
        validate_email('s@muelcolvin.com')
        m.assert_called_once()


def test_import_email_validator_not_installed(mocker):
    mocker.patch.dict('sys.modules', {'email_validator': None})
    with pytest.raises(ImportError, match=r'email-validator is not installed, run `pip install \'pydantic\[email\]\'`'):
        import_email_validator()


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_import_email_validator_invalid_version(mocker):
    mocker.patch('pydantic.networks.version', return_value='1.0.0')
    with pytest.raises(
        ImportError, match=r'email-validator version >= 2.0 required, run pip install -U email-validator'
    ):
        import_email_validator()


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_name_email():
    class Model(BaseModel):
        v: NameEmail

    assert str(Model(v=NameEmail('foo bar', 'foobaR@example.com')).v) == 'foo bar <foobaR@example.com>'
    assert str(Model(v='foo bar  <foobaR@example.com>').v) == 'foo bar <foobaR@example.com>'
    assert str(Model(v='foobaR@example.com').v) == 'foobaR <foobaR@example.com>'
    assert NameEmail('foo bar', 'foobaR@example.com') == NameEmail('foo bar', 'foobaR@example.com')
    assert NameEmail('foo bar', 'foobaR@example.com') != NameEmail('foo bar', 'different@example.com')

    assert Model.model_validate_json('{"v":"foo bar <foobaR@example.com>"}').v == NameEmail(
        'foo bar', 'foobaR@example.com'
    )
    assert str(Model.model_validate_json('{"v":"foobaR@example.com"}').v) == 'foobaR <foobaR@example.com>'
    assert (
        Model(v=NameEmail('foo bar', 'foobaR@example.com')).model_dump_json() == '{"v":"foo bar <foobaR@example.com>"}'
    )

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1)
    assert exc_info.value.errors() == [
        {'input': 1, 'loc': ('v',), 'msg': 'Input is not a valid NameEmail', 'type': 'name_email_type'}
    ]


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_name_email_serialization():
    class Model(BaseModel):
        email: NameEmail

    m = Model.model_validate({'email': '"name@mailbox.com" <name@mailbox.com>'})
    assert m.email.name == 'name@mailbox.com'
    assert str(m.email) == '"name@mailbox.com" <name@mailbox.com>'

    obj = json.loads(m.model_dump_json())
    Model(email=obj['email'])


def test_specialized_urls() -> None:
    ta = TypeAdapter(HttpUrl)

    http_url = ta.validate_python('http://example.com/something')
    assert str(http_url) == 'http://example.com/something'
    assert repr(http_url) == "HttpUrl('http://example.com/something')"
    assert http_url.__class__ == HttpUrl
    assert http_url.host == 'example.com'
    assert http_url.path == '/something'
    assert http_url.username is None
    assert http_url.password is None

    http_url2 = ta.validate_python(http_url)
    assert str(http_url2) == 'http://example.com/something'
    assert repr(http_url2) == "HttpUrl('http://example.com/something')"
    assert http_url2.__class__ == HttpUrl
    assert http_url2.host == 'example.com'
    assert http_url2.path == '/something'
    assert http_url2.username is None
    assert http_url2.password is None
    assert http_url.encoded_string() == 'http://example.com/something'
    assert http_url2.encoded_string() == 'http://example.com/something'


def test_url_equality() -> None:
    # works for descendants of _BaseUrl and _BaseMultiHostUrl
    assert HttpUrl('http://example.com/something') == HttpUrl('http://example.com/something')
    assert PostgresDsn('postgres://user:pass@localhost:5432/app') == PostgresDsn(
        'postgres://user:pass@localhost:5432/app'
    )


def test_encode_multi_host_url() -> None:
    multi_host_url_postgres = PostgresDsn('postgres://user:pass@localhost:5432/app')
    multi_host_url_http_url = HttpUrl('http://example.com/something')

    assert multi_host_url_postgres.encoded_string() == 'postgres://user:pass@localhost:5432/app'
    assert multi_host_url_http_url.encoded_string() == 'http://example.com/something'


def test_equality_independent_of_init() -> None:
    ta = TypeAdapter(HttpUrl)
    from_str = ta.validate_python('http://example.com/something')
    from_url = ta.validate_python(HttpUrl('http://example.com/something'))
    from_validated = ta.validate_python(from_str)

    assert from_str == from_url == from_validated


def test_url_subclasses_any_url() -> None:
    http_url = AnyHttpUrl('https://localhost')
    assert isinstance(http_url, AnyUrl)
    assert isinstance(http_url, AnyHttpUrl)

    url = TypeAdapter(AnyUrl).validate_python(http_url)
    assert url is http_url


def test_custom_constraints() -> None:
    HttpUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=['http', 'https'])]
    ta = TypeAdapter(HttpUrl)
    assert ta.validate_python('https://example.com')

    with pytest.raises(ValidationError):
        ta.validate_python('ftp://example.com')


def test_after_validator() -> None:
    def remove_trailing_slash(url: AnyUrl) -> str:
        """Custom url -> str transformer that removes trailing slash."""
        return str(url._url).rstrip('/')

    HttpUrl = Annotated[
        AnyUrl,
        UrlConstraints(allowed_schemes=['http', 'https']),
        AfterValidator(lambda url: remove_trailing_slash(url)),
    ]
    ta = TypeAdapter(HttpUrl)
    assert ta.validate_python('https://example.com/') == 'https://example.com'


def test_serialize_as_any() -> None:
    ta = TypeAdapter(Any)
    assert ta.dump_python(HttpUrl('https://example.com')) == HttpUrl('https://example.com/')
    assert ta.dump_json('https://example.com') == b'"https://example.com"'


def test_any_url_hashable() -> None:
    example_url_1a = AnyUrl('https://example1.com')
    example_url_1b = AnyUrl('https://example1.com')
    example_url_2 = AnyUrl('https://example2.com')

    assert hash(example_url_1a) == hash(example_url_1b)
    assert hash(example_url_1a) != hash(example_url_2)
    assert len({example_url_1a, example_url_1b, example_url_2}) == 2

    example_multi_host_url_1a = PostgresDsn('postgres://user:pass@host1:5432,host2:5432/app')
    example_multi_host_url_1b = PostgresDsn('postgres://user:pass@host1:5432,host2:5432/app')
    example_multi_host_url_2 = PostgresDsn('postgres://user:pass@host1:5432,host3:5432/app')

    assert hash(example_multi_host_url_1a) == hash(example_multi_host_url_1b)
    assert hash(example_multi_host_url_1a) != hash(example_multi_host_url_2)
    assert len({example_multi_host_url_1a, example_multi_host_url_1b, example_multi_host_url_2}) == 2


def test_host_not_required_for_2_9_compatibility() -> None:
    data_uri = 'file:///path/to/data'
    url = AnyUrl(data_uri)
    assert url.host is None


def test_json_schema() -> None:
    ta = TypeAdapter(HttpUrl)
    val_json_schema = ta.json_schema(mode='validation')
    assert val_json_schema == {'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2083}

    ser_json_schema = ta.json_schema(mode='serialization')
    assert ser_json_schema == {'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2083}


def test_any_url_comparison() -> None:
    first_url = AnyUrl('https://a.com')
    second_url = AnyUrl('https://b.com')

    assert first_url < second_url
    assert second_url > first_url
    assert first_url <= second_url
    assert second_url >= first_url


def test_max_length_base_url() -> None:
    class Model(BaseModel):
        url: AnyUrl = Field(max_length=20)

    # _BaseUrl/AnyUrl adds trailing slash: https://github.com/pydantic/pydantic/issues/7186
    # once solved the second expected line can be removed
    expected = 'https://example.com'
    expected = f'{expected}/'
    assert len(Model(url='https://example.com').url) == len(expected)

    with pytest.raises(ValidationError, match=r'Value should have at most 20 items after validation'):
        Model(url='https://example.com/longer')


def test_max_length_base_multi_host() -> None:
    class Model(BaseModel):
        postgres: PostgresDsn = Field(max_length=45)

    expected = 'postgres://user:pass@localhost:5432/foobar'
    assert len(Model(postgres=expected).postgres) == len(expected)

    with pytest.raises(ValidationError, match=r'Value should have at most 45 items after validation'):
        Model(postgres='postgres://user:pass@localhost:5432/foobarbazfoo')


def test_unexpected_ser() -> None:
    ta = TypeAdapter(HttpUrl)
    with pytest.raises(
        PydanticSerializationError,
        match="Expected `<class 'pydantic.networks.HttpUrl'>` but got `<class 'str'>` with value `'http://example.com'`",
    ):
        ta.dump_python('http://example.com', warnings='error')


def test_url_ser() -> None:
    ta = TypeAdapter(HttpUrl)
    assert ta.dump_python(HttpUrl('http://example.com')) == HttpUrl('http://example.com')
    assert ta.dump_json(HttpUrl('http://example.com')) == b'"http://example.com/"'


def test_url_ser_as_any() -> None:
    ta = TypeAdapter(Any)
    assert ta.dump_python(HttpUrl('http://example.com')) == HttpUrl('http://example.com')
    assert ta.dump_json(HttpUrl('http://example.com')) == b'"http://example.com/"'
