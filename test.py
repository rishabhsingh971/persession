""" Test file for login module. """
import re
from getpass import getpass

from login import Login


def set_auth_data(session, url, data):
    """
    set authentication data

    Arguments:
        session -- requests session object
        url {str} -- url
        data {dict} -- login payload
    """
    data['user[email]'] = input('user email : ')
    data['user[password]'] = getpass('password   : ')

    res = session.get(url)
    pattern = '<form id.*<input type="hidden" name="authenticity_token" value="(.*?)"'
    match = re.search(pattern, res.text)
    if match:
        data['authenticity_token'] = match.group(1)


def main():
    """ main function. """
    base_url = 'https://www.interviewbit.com'
    practice_url = base_url + '/practice'
    login_url = base_url + '/users/sign_in/'
    login_data = {
        'user[remember_me]': '1',
        'utf8': '&#x2713;',
        'commit': 'Log in',
    }
    Login(login_url, login_data, practice_url, 'Log Out', debug=True,
          before_login=lambda session, login_data: set_auth_data(session, login_url, login_data))


if __name__ == "__main__":
    main()
