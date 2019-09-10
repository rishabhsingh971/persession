""" Test file for login module. """
import re
from getpass import getpass

from persession import Session, LoginInfo


def set_auth_data(session: Session, url: str):
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
    session.update_login_info_data(data)


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
    info = LoginInfo(login_url, login_data, practice_url, 'Log Out')
    Session(info, debug=True,
            before_login=lambda sess: set_auth_data(sess, login_url))


if __name__ == "__main__":
    main()
