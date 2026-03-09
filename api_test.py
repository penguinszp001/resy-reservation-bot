import requests

if __name__ == "__main__":

    url = "https://api.resy.com/4/find"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-Origin": "https://resy.com",
        "Authorization": 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
        "X-Resy-Auth-Token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NzY5NzU3NzUsInVpZCI6NTI4MjA5MDYsImd0IjoiY29uc3VtZXIiLCJncyI6W10sImxhbmciOiJlbi11cyIsImV4dHJhIjp7Imd1ZXN0X2lkIjoxNjEzMjQ0NzB9fQ.AbEiTAD2ZkySnQBtjCGdhStlhhpmY51am9IqbAGmrYYE2rgaiPkZsmTLS_osgCFvbtgxYxurr677LgMDh9mPJVR6ANUCIpmsaZXa9L-_uf0oAMNY5GAGGgwu5aU_xoUwWPcVi-YwFP511D1ag4YjClyWdErglt4T6oCNHlRmcSviw9oR",
        "X-Resy-Universal-Auth": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NzY5NzU3NzUsInVpZCI6NTI4MjA5MDYsImd0IjoiY29uc3VtZXIiLCJncyI6W10sImxhbmciOiJlbi11cyIsImV4dHJhIjp7Imd1ZXN0X2lkIjoxNjEzMjQ0NzB9fQ.AbEiTAD2ZkySnQBtjCGdhStlhhpmY51am9IqbAGmrYYE2rgaiPkZsmTLS_osgCFvbtgxYxurr677LgMDh9mPJVR6ANUCIpmsaZXa9L-_uf0oAMNY5GAGGgwu5aU_xoUwWPcVi-YwFP511D1ag4YjClyWdErglt4T6oCNHlRmcSviw9oR",
        "Origin": "https://resy.com",
        "Referer": "https://resy.com/",
    }

    payload = '{"lat":0,"long":0,"day":"2026-03-21","party_size":2,"venue_id":73777}'

    response = requests.post(url, headers=headers, json=payload)

    print(response.status_code)
    print(response.text)


