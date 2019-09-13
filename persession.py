""" Persistent session with login helper that can help python scripts to login to sites"""
import logging
import logging.config
import os
import pickle
import tempfile
from enum import Enum, unique, auto
from datetime import datetime

import requests

# create logger with module name
L = logging.getLogger(__name__)
L.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
FILE_HANDLER = logging.handlers.RotatingFileHandler(
    os.path.join(tempfile.gettempdir(), 'session_login.log'), maxBytes=512000, backupCount=5)
FILE_HANDLER.setLevel(logging.DEBUG)
# create console handler with a higher log level
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.ERROR)
# create formatter and add it to the handlers
FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
FILE_HANDLER.setFormatter(FORMATTER)
CONSOLE_HANDLER.setFormatter(FORMATTER)
# add the handlers to the logger
L.addHandler(FILE_HANDLER)
L.addHandler(CONSOLE_HANDLER)


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
    SUCCESS = 'Login Succesful'
    FAILURE = 'Login Failed'
    LOGGED_IN = 'Already logged in'


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
    """Persistent session with login helper and proxy support. Basic Usage:
        >>> data = {'user': 'user', 'password': 'pass'}
        >>> login_info = LoginInfo('https://e.com/log_in', data, 'https://e.com/home', 'log out')
        >>> session = Session(login_info)
        >>> res = session.get('https://e.com/data')
    """

    def __init__(
            self,
            cache_file_path: str,
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
        if debug:
            CONSOLE_HANDLER.setLevel(logging.DEBUG)
        self.cache_file_path = cache_file_path if cache_file_path else get_temp_file_path(
            prefix=Session.__name__, suffix='.dat')
        self.load_session()

    def login(
            self,
            url: str,
            data: dict,
            **kwargs
    ) -> dict:
        """Login to the session. tries to read last saved session from cache file,
        If this fails or last cache access was too old do proper login.

        Arguments:
            url {str} -- login url
            data {dict} -- login data payload

        Keyword Arguments:
            force_login {bool} -- bypass session cache and re-login (default: {False})

        Returns:
            {dict} -- dictionary with login status and request response
        """
        if self.is_logged_in(url):
            L.debug(LoginStatus.LOGGED_IN.value)
            return {'status': LoginStatus.LOGGED_IN.value, 'response': None}

        L.debug('Try to Login - %s', url)
        res = self.post(url, data, **kwargs)

        if self.is_logged_in(url):
            if self.cache_type == CacheType.AFTER_EACH_LOGIN:
                self.cache_session()
            return {'status': LoginStatus.SUCCESS.value, 'response': res}
        return {'status': LoginStatus.FAILURE.value, 'response': res}

    def load_session(self) -> bool:
        """Load session from cache

        Returns:
            bool -- if session loaded
        """
        L.debug('Check session cache')
        if not os.path.exists(self.cache_file_path):
            L.debug('Cache file not found')
            return False

        time = datetime.fromtimestamp(
            os.path.getmtime(self.cache_file_path))
        # only load if last access time of file is less than max session time
        last_modified_time = (datetime.now() - time).seconds
        L.debug('Cache file found (last accessed %ss ago)', last_modified_time)

        if last_modified_time < self.cache_timeout:
            with open(self.cache_file_path, "rb") as file:
                session = pickle.load(file)
                if not isinstance(session, Session):
                    L.debug('Cache file corrupted')
                    return False
                self.__dict__.update(session.__dict__)
                L.debug('Cached session restored')
            return True
        L.debug('Cache expired (older than %s)', self.cache_timeout)
        return False

    def cache_session(self):
        """Save session to a cache file."""
        # always save (to update timeout)
        L.debug('Cache Session')
        with open(self.cache_file_path, "wb") as file:
            pickle.dump(self, file)

    def is_logged_in(self, login_url: str) -> bool:
        """Return if logged in

        Arguments:
            login_url {str} -- login url
        Returns:
            bool -- log in status
        """
        L.debug('Check login - %s', login_url)
        if not login_url:
            return False
        res = self.get(login_url, allow_redirects=False)
        if res.status_code == 302:
            L.debug('Is logged in')
            return True
        L.debug('Is not logged in')
        return False

    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        prep = super().prepare_request(request)
        if self.cache_type == CacheType.AFTER_EACH_REQUEST or (
                self.cache_type == CacheType.AFTER_EACH_POST and
                request.method and request.method.tolower() == 'post'
        ):
            self.cache_session()
        return prep
