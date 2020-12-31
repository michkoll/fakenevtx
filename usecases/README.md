# Use Cases

Please make sure, that all installation requirements (e.g. installed packages in virtual environment) are fulfilled

## 001 Replace username

See [001_replace_username.py](001_replace_username.py)

```shell
$ python3 -m usecases.001_replace_username -h
usage: 001_replace_username.py [-h] src dest old_username new_username new_sid

Replace a given username with new value.

positional arguments:
  src           Path to the source Windows EVTX event log file
  dest          Path to the source Windows EVTX event log file
  old_username  Old username
  new_username  New username
  new_sid       SID of new user

optional arguments:
  -h, --help    show this help message and exit
```

| Original      | Result  |
| ------------- |:-------------:| 
| ![Use Case 001 - Original](../doc/images/001_original.png "Use Case 001 - Original")     | ![Use Case 001 - Result](../doc/images/001_result.png "Use Case 001 - Result") | 

