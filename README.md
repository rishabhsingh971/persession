# persession
A wrapper on requests.Session with following additional functionalities:
- Persistance: session can be cached in a file.
- Login functionalities: login and is_logged_in functions are available to help logging into sites


### Usage
```python
from persession import Session, LoginStatus

base_url = 'https://e.com'
cache_file_path = 'cache.dat'
session = Session(cache_file_path)

is_logged_in = session.is_logged_in()
if not is_logged_in:
    login_url = base_url + '/login'
    data = {'user': 'user', 'password': 'pass'}
    res = session.login(login_url)
    if res.login_status = LoginStatus.SUCCESS:
        is_logged_in = True
        print('Login success')
    else:
        print('login failed')
if is_logged_in:
    data_url = base_url + '/data'
    res = session.get(data_url)
```
You can also check out [example.py](./example.py) for a detailed example.