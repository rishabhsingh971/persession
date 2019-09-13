""" Test file for login module. """
import os
import re
from getpass import getpass

from persession import Session


def get_auth_data(session: Session, url: str):
    """
    set authentication data

    Arguments:
        session {Sessioni} -- Session instance
        url {str} -- url
    """
    # if you don't want to enter user and password everytime
    # insert user and password in environment with keys below or replace them manually here
    user = os.environ.get('PSTEST_USER')
    password = os.environ.get('PSTEST_PASSWORD')
    auth_data = {
        'user[email]': user if user else input('user email : '),
        'user[password]': password if password else getpass('password   : ')
    }

    res = session.get(url)
    pattern = '<form id.*<input type="hidden" name="authenticity_token" value="(.*?)"'
    match = re.search(pattern, res.text)
    if match:
        auth_data['authenticity_token'] = match.group(1)
    return auth_data


def main():
    """main function"""
    cache_file_path = 'cache.dat'
    session = Session(cache_file_path, debug=True)

    base_url = 'https://www.interviewbit.com'
    login_url = base_url + '/users/sign_in/'
    login_data = {
        'user[remember_me]': '1',
        'utf8': '&#x2713;',
        'commit': 'Log in',
    }

    is_logged_in = session.is_logged_in(login_url)
    if not is_logged_in:
        auth_data = get_auth_data(session, login_url)
        login_data.update(auth_data)
        session.login(login_url, login_data)

    print(is_logged_in)


if __name__ == "__main__":
    main()
