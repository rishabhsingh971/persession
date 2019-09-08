""" Login Helper for python scripts which need to login to a site """
import os
import pickle
from datetime import datetime
from urllib.parse import urlparse

import requests

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
DEFAULT_SESSION_TIMEOUT = 60 * 60


class Login:
    """
    A class which handles and saves login sessions with proxy support. Basic Usage:
    >>> base_url = 'https://example.com/'
    >>> login_url = base_url + 'log_in'
    >>> login_data = {'user': 'user', 'password': 'pass'}
    >>> site = Login(slogin_url, login_data, base_url + 'user_page', 'log out')
    >>> res = site.get(base_url + 'data')
    """

    def __init__(
            self,
            login_url,
            login_data,
            login_test_url,
            login_test_string,
            before_login=None,
            max_session_time_seconds=DEFAULT_SESSION_TIMEOUT,
            proxies=None,
            user_agent=DEFAULT_USER_AGENT,
            debug=True,
            force_login=False,
            **kwargs
    ):
        url_data = urlparse(login_url)

        self.login_data = login_data
        self.login_url = login_url
        self.login_test_url = login_test_url
        self.proxies = proxies
        self.max_session_time = max_session_time_seconds
        self.session_file = url_data.netloc + '.dat'
        self.user_agent = user_agent
        self.login_test_string = login_test_string
        self.debug = debug
        self.before_login = before_login
        self.login(force_login, **kwargs)

    def login(self, force_login=False, **kwargs):
        is_cached = False
        if self.debug:
            print('loading or generating session...')
        if os.path.exists(self.session_file) and not force_login:
            time = datetime.fromtimestamp(os.path.getmtime(self.session_file))

            # only load if last access time of file is less than max session time
            last_modified_time = (datetime.now() - time).seconds
            if last_modified_time < self.max_session_time:
                with open(self.session_file, "rb") as f:
                    self.session = pickle.load(f)
                    is_cached = True
                    if self.debug:
                        print("loaded session from cache (last accessed {}s ago)".format(
                            last_modified_time))
        if not is_cached:
            self.session = requests.Session()
            if self.user_agent:
                self.session.headers.update({'user-agent': self.user_agent})
            if self.before_login:
                self.before_login(self.session, self.login_data)
            self.session.post(self.login_url, data=self.login_data,
                              proxies=self.proxies, **kwargs)

        # test login
        res = self.session.get(self.login_test_url)
        if res.text.lower().find(self.login_test_string.lower()) < 0:
            raise Exception(
                'could not log into provided site "{}" (did not find successful login string)'
                .format(self.login_url)
            )
        if self.debug:
            print('successfully created new session with login')
        self.cache_session()

    def cache_session(self):
        # always save (to update timeout)
        with open(self.session_file, "wb") as f:
            pickle.dump(self.session, f)
            if self.debug:
                print('updated session cache-file {}'.format(self.session_file))

    def get(self, url, **kwargs):
        res = self.session.get(url, proxies=self.proxies, **kwargs)
        # the session has been updated on the server, so also update in cache
        self.cache_session()
        return res

    def post(self, url, data, **kwargs):
        res = self.session.post(
            url, data=data, proxies=self.proxies, **kwargs)
        self.cache_session()
        return res
