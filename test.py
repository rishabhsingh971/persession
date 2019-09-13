""" Test file for login module. """
import re
from getpass import getpass

from persession import Session, LoginInfo


def get_auth_data(session: Session, url: str):
    """
    set authentication data

    Arguments:
        session {Sessioni} -- Session instance
        url {str} -- url
    """
    data = {
        'user[email]': input('user email : '),
        'user[password]': getpass('password   : ')
    }

    res = session.get(url)
    pattern = '<form id.*<input type="hidden" name="authenticity_token" value="(.*?)"'
    match = re.search(pattern, res.text)
    if match:
        data['authenticity_token'] = match.group(1)
    return data


def main():
    """ main function. """
    cache_file_path = 'cache.dat'
    session = Session(cache_file_path, debug=True)

    base_url = 'https://www.interviewbit.com'
    practice_url = base_url + '/practice'
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
        info = LoginInfo(login_url, login_data, practice_url, 'Log Out')
        session.login(info)

    print(is_logged_in)


if __name__ == "__main__":
    main()
