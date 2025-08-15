import select
import psycopg2
import psycopg2.extensions
import math
import time
import os
import requests
import json
import base64
import subprocess

class Config:
    APIKEY = ""
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_PASS = os.getenv("DB_PASS")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    TRIGGER_TEXT = '''
CREATE OR REPLACE FUNCTION notify_content_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('content_update', NEW.key::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE TRIGGER store_update_trigger
AFTER INSERT OR UPDATE ON store
FOR EACH ROW
EXECUTE PROCEDURE notify_content_update();
'''

def init():
    with open("/APIKEY.txt", 'r') as f:
        Config.APIKEY = f.readline().strip()
    conn = psycopg2.connect(dbname=Config.DB_NAME, user=Config.DB_USER, host=Config.DB_HOST, password=Config.DB_PASS)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(Config.TRIGGER_TEXT)
    cur.execute("LISTEN content_update;")
    return (conn, cur)


def update_pad(padid):
    myparams = {
        "apikey": Config.APIKEY,
        "padID": padid
    }
    r = requests.get("http://app:9001/api/1/getText", params = myparams)
    print(r.url)
    if r.status_code == requests.codes.ok:
        print(r.text)
    else:
        print(f"error with pad {padid}")
        return
    data = json.loads(r.text)
    if data["code"] != 0:
        print(f"http api error on pad {padid}, return {r.text}")
        return
    print(data["data"]["text"])
    encoded_name = base64.b64encode(padid.encode("UTF-8")).decode("UTF-8")
    print(encoded_name)
    with open(f"/typ/{encoded_name}.typ", "w") as f:
        f.write(data["data"]["text"])
    if padid not in watched_pads:
        watched_pads.add(padid)
        os.system(f"typst watch /typ/{encoded_name}.typ /pdf/{encoded_name}.pdf &")
        # subprocess.run(['typst', 'watch', f'/typ/{encoded_name}.typ', f'/pdf/{encoded_name}.pdf'], check=True)
    return

def run_loop(conn, cur):
  while True:
      if select.select([conn], [], [], 5) == ([], [], []):
          print("Timeout")
      else:
          conn.poll()
          while conn.notifies:
              notify = conn.notifies.pop(0)
              print(f"get notify: {notify.payload}")
              s = notify.payload
              if len(s) >= 3 and s[0:3] == "pad":
                  pad = s.split(":")[1]
                  update_pad(pad)
  return

if __name__ == "__main__":
    global watched_pads
    watched_pads = set()
    conn, cur = init()
    run_loop(conn, cur)
