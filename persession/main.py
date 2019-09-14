"""A Wrapper on requests.Session with persistence across script runs(caching in a file)
and login helper that can help python scripts to login to sites"""
import logging
import logging.config
import os
import pickle
import tempfile
from datetime import datetime
from enum import Enum, auto, unique

import requests


DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
DEFAULT_CACHE_TIMEOUT = 60 * 60


@unique
class CacheType(Enum):
    """Session Cache types"""
    MANUAL = auto()
    AFTER_EACH_REQUEST = auto()
    AFTER_EACH_POST = auto()
    AFTER_EACH_LOGIN = auto()


@unique
class LoginStatus(Enum):
    """Login Status"""
    SUCCESS = 'Login Successful'
    FAILURE = 'Login Failed'


class LoginResponse(requests.Response):
    """requests response wrapper with login status"""

    def __init__(self, login_status: LoginStatus, response: requests.Response = None):
        """initializer

        Arguments:
            login_status {LoginStatus} -- login status
        """
        super().__init__()
        self.login_status = login_status
        if response:
            self.__dict__.update(response.__dict__)


def get_temp_file_path(prefix, suffix) -> str:
    """get a temporary file path
    Returns:
        {str} -- file path
    """
    temp_file = file_path = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            prefix=prefix, suffix=suffix, delete=False)
        file_path = temp_file.name()
    finally:
        if temp_file:
            temp_file.close()
    return file_path


class Session(requests.Session):
    """Persistent session with login helper.
    Basic Usage:
        >>> cache_file_path = 'cache.dat'
        >>> session = Session(cache_file_path)
        >>> is_logged_in = session.is_logged_in()
        >>> if not is_logged_in:
        >>>     data = {'user': 'user', 'password': 'pass'}
        >>>     res = session.login('https://e.com/login', data)
        >>>     print(res.login_status)
        >>> res = session.get('https://e.com/data')
    """

    def __init__(
            self,
            cache_file_path: str = None,
            cache_timeout: int = DEFAULT_CACHE_TIMEOUT,
            cache_type: CacheType = CacheType.AFTER_EACH_LOGIN,
            proxies: dict = None,
            user_agent: str = DEFAULT_USER_AGENT,
            debug: bool = False,
    ):
        """Initializer

        Arguments:
            login_info {LoginInfo} -- login info

        Keyword Arguments:
            cache_file_path {int} -- session cache file's path (default: {None})
            cache_timeout {int} -- session timeout in seconds (default: {3600})
            cache_type {CacheType} -- type of caching determines when session is cached
                (default: {CacheType.ON_EXIT})
            proxies {dict} -- proxies in format {'https': 'https://user:pass@server:port',
                'http' : ...} (default: {None})
            user_agent {str} -- user agent (default:
                {'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'})
            debug {bool} -- verbose log messages (default: {False})

        Returns:
            Session -- Session class instance
        """
        super().__init__()
        self.cache_timeout = cache_timeout
        self.cache_type = cache_type
        if proxies:
            self.proxies.update(proxies)
        if user_agent:
            self.headers.update({'user-agent': user_agent})
        self.init_logger(debug)
        self.cache_file_path = cache_file_path if cache_file_path else get_temp_file_path(
            prefix=Session.__name__, suffix='.dat')
        self.load_session()

    def init_logger(self, debug):
        """ initialize logger """
        # create logger with package name
        self.logger = logging.getLogger(__package__)
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(tempfile.gettempdir(), __package__+'.log'), maxBytes=512000, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)-5s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.d = self.logger.debug
        self.i = self.logger.info

    def login(
            self,
            url: str,
            data: dict,
            **kwargs
    ) -> LoginResponse:
        """Login to the session. tries to read last saved session from cache file,
        If this fails or last cache access was too old do proper login.

        Arguments:
            url {str} -- login url
            data {dict} -- login data payload

        Keyword Arguments:
            force_login {bool} -- bypass session cache and re-login (default: {False})

        Returns:
            {LoginResponse} -- requests response with login status
        """
        self.i('Try to Login - %s', url)
        res = self.post(url, data, **kwargs)

        if self.is_logged_in(url):
            if self.cache_type == CacheType.AFTER_EACH_LOGIN:
                self.cache_session()
            return LoginResponse(LoginStatus.SUCCESS, res)
        return LoginResponse(LoginStatus.FAILURE, res)

    def load_session(self) -> bool:
        """Load session from cache

        Returns:
            bool -- if session loaded
        """
        self.i('Check session cache')
        if not os.path.exists(self.cache_file_path):
            self.i('Cache file not found')
            return False

        time = datetime.fromtimestamp(
            os.path.getmtime(self.cache_file_path))
        # only load if last access time of file is less than max session time
        last_modified_time = (datetime.now() - time).seconds
        self.i('Cache file found (last accessed %ss ago)', last_modified_time)

        if last_modified_time < self.cache_timeout:
            with open(self.cache_file_path, "rb") as file:
                session = pickle.load(file)
                if not isinstance(session, Session):
                    self.i('Cache file corrupted')
                    return False
                self.__dict__.update(session.__dict__)
                self.i('Cached session restored')
            return True
        self.i('Cache expired (older than %s)', self.cache_timeout)
        return False

    def cache_session(self):
        """Save session to a cache file."""
        # always save (to update timeout)
        self.i('Cache Session')
        with open(self.cache_file_path, "wb") as file:
            pickle.dump(self, file)

    def is_logged_in(self, login_url: str) -> bool:
        """Return if logged in

        Arguments:
            login_url {str} -- login url
        Returns:
            bool -- log in status
        """
        self.d('Check login - %s', login_url)
        if not login_url:
            return False
        res = self.get(login_url, allow_redirects=False)
        if res.status_code == 302:
            self.i('Is logged in')
            return True
        self.i('Is not logged in')
        return False

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:
        res = super().send(request, **kwargs)
        if self.cache_type == CacheType.AFTER_EACH_REQUEST or (
                self.cache_type == CacheType.AFTER_EACH_POST and
                request.method and request.method.lower() == 'post'
        ):
            self.cache_session()
        return res

    def get_cache_file_path(self) -> str:
        """get cache file's path

        Returns:
            str -- cache file's path
        """
        return self.cache_file_path
