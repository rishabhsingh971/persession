""" Login Helper for python scripts which need to login to a site """
import logging
import logging.config
import os
import pickle
import tempfile
from datetime import datetime
from urllib.parse import urlparse

import requests

# create logger with module name
L = logging.getLogger(__name__)
L.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
FILE_HANDLER = logging.handlers.RotatingFileHandler(
    'session_login.log', maxBytes=512000, backupCount=5)
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
DEFAULT_SESSION_TIMEOUT = 60 * 60


class LoginInfo:
    """ Login Info """

    def __init__(self, url: str, data: dict, test_url: str, test_string: str):
        """Initializer

        Arguments:
            url {str} -- login url
            data {dict} -- login data or payload
            test_url {str} -- login test url
            test_string {str} -- string that would be checked in get response of give test url
        """
        self.url = url
        self.data = data
        self.test_url = test_url
        self.test_string = test_string

    def update_data(self, data: dict):
        """update login data

        Arguments:
            data {dict} -- [description]
        """
        self.data.update(data)


class Login:
    """A class which handles and saves login sessions with proxy support. Basic Usage:
        >>> login_data = {'user': 'user', 'password': 'pass'}
        >>> site = Login('https://e.com/log_in', login_data, 'https://e.com/user_page', 'log out')
        >>> res = site.get('https://e.com/data')
    """

    def __init__(
            self,
            login_info: LoginInfo,
            before_login=None,
            max_session_time: int = DEFAULT_SESSION_TIMEOUT,
            proxies: dict = None,
            user_agent: str = DEFAULT_USER_AGENT,
            debug: bool = True,
            force_login: bool = False,
            **kwargs
    ):
        """Initializer

        Arguments:
            login_info {LoginInfo} -- login info

        Keyword Arguments:
            before_login {callback} -- function to call before login,
                with session and login data as arguments (default: {None})
            max_session_time {int} -- session timeout in seconds (default: {3600})
            proxies {dict} -- proxies in format {'https': 'https://user:pass@server:port',
                'http' : ...
            user_agent {str} -- user agent (default:
                {'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'})
            debug {bool} -- verbose log messages (default: {True})
            force_login {bool} -- bypass session cache and relogin (default: {False})

        Raises:
            Exception: when login test fails

        Returns:
            Login -- Login class instance
        """
        url_data = urlparse(login_info.url)

        self.login_data = login_info.data
        self.login_url = login_info.url
        self.login_test_url = login_info.test_url
        self.proxies = proxies
        self.max_session_time = max_session_time
        self.session_cache_path = os.path.join(
            tempfile.gettempdir(), url_data.netloc + '.dat')
        L.debug('Set session cache file path - "%s"', self.session_cache_path)
        self.user_agent = user_agent
        self.login_test_string = login_info.test_string
        if debug:
            CONSOLE_HANDLER.setLevel(logging.DEBUG)
        self.before_login = before_login
        self.__is_logged_in = False
        self.session: requests.Session = None
        self.login(force_login, **kwargs)

    def login(self, force_login: bool = False, **kwargs):
        """Login to the session. tries to read last saved session from cache file,
        If this fails or last cache access was too old do proper login.
        Always updates session cache file.
        """
        is_cached = False
        L.debug('Ignore cache(force login)' if force_login else 'Check session cache')
        if os.path.exists(self.session_cache_path) and not force_login:
            time = datetime.fromtimestamp(
                os.path.getmtime(self.session_cache_path))
            # only load if last access time of file is less than max session time
            last_modified_time = (datetime.now() - time).seconds
            L.debug('Cache file found (last accessed %ss ago)',
                    last_modified_time)

            if last_modified_time < self.max_session_time:
                with open(self.session_cache_path, "rb") as file:
                    self.session = pickle.load(file)
                is_cached = True
            else:
                L.debug('Cache expired (older than %s)', self.max_session_time)
        if not is_cached:
            L.debug('Generate new login session')
            self.session = requests.Session()
            if self.user_agent:
                self.session.headers.update({'user-agent': self.user_agent})
            if self.before_login:
                L.debug('Call before login callback')
                self.before_login(self.session, self.login_data)
            self.session.post(self.login_url, data=self.login_data,
                              proxies=self.proxies, **kwargs)

        self._test_login()
        L.debug('Cached session restored' if is_cached else 'Login successfull')
        self.cache_session()

    def cache_session(self):
        """Save session to a cache file."""
        # always save (to update timeout)
        L.debug('Update session cache file')
        with open(self.session_cache_path, "wb") as file:
            pickle.dump(self.session, file)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Get request

        Arguments:
            url {str} -- url

        Returns:
            requests.Response -- request response
        """
        L.debug('Get request %s', url)
        res = self.session.get(url, proxies=self.proxies, **kwargs)
        # the session has been updated on the server, so also update in cache
        self.cache_session()
        return res

    def post(self, url: str, data: dict, **kwargs) -> requests.Response:
        """Post request

        Arguments:
            url {str} -- url
            data {dict} -- data

        Returns:
            requests.Response -- request response
        """
        L.debug('Post request %s', url)
        res = self.session.post(
            url, data=data, proxies=self.proxies, **kwargs)
        # the session has been updated on the server, so also update in cache
        self.cache_session()
        return res

    def _test_login(self):
        """Test login

        Raises:
            Exception: Login test failed
        """
        if not self.login_test_url or not self.login_test_string:
            return
        L.debug('Test login')
        res = self.session.get(self.login_test_url)
        if res.text.lower().find(self.login_test_string.lower()) < 0:
            raise Exception('Login test failed: url - "{}",string - "{}"'.format(
                self.login_test_url, self.login_test_string))
        self.__is_logged_in = True
        L.debug('Login test pass')

    def is_logged_in(self):
        """return if logged in (works only if test url and string is given)

        Returns:
            bool -- log in status
        """
        return self.__is_logged_in
