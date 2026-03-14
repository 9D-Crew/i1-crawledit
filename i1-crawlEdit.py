print("i1-crawlEdit (C) 2026 9D Crew\nConnecting to i1...")
import paramiko; import configparser; import ast; import sys; import time; import os; import subprocess; import json

config = configparser.ConfigParser(); config.read('config.ini'); ssh_config = config['SSH']
ip = ssh_config.get('IP'); port = ssh_config.getint('PORT')
username = ssh_config.get('USERNAME'); password = ssh_config.get('PASSWORD')
ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=ip, port=port, username=username, password=password); sftp = ssh.open_sftp()

stdin, stdout, stderr = ssh.exec_command("perl -e 'print time, \"\\n\";'")
epoch = stdout.read().decode().strip()

os.makedirs("./temp", exist_ok=True)
print("loading datastore...")
sftp.get("/twc/data/datastore/ds.dat", "./temp/ds.dat")
sftp.get("/twc/data/datastore/ds.stat", "./temp/ds.stat")
sftp.close(); ssh.close()

if sys.platform.startswith("win"):
    pypath = "py"
else:
    pypath = "python3"
subprocess.run([pypath, "loadi1datastore.py", "./temp"])
# okay we have successfully stolen code
print("Loading crawls...")

# okay we need to load the crawls into our format now from the renderE format.
# better then dealing with the datastore directly! not by much though...
with open("ds.json", 'r') as datastore:
    jsondata = json.load(datastore)

serialNum = jsondata['Config.1.LASCrawl.serialNum'][0]
crawls = []
i = 0
while f"Config.1.Ldl_LASCrawl.crawls.{i}.0" in jsondata:
    start_time = int(jsondata[f"Config.1.Ldl_LASCrawl.crawls.{i}.0"][0])
    end_time = int(jsondata[f"Config.1.Ldl_LASCrawl.crawls.{i}.1"][0])
    windows = []
    j = 0
    while f"Config.1.Ldl_LASCrawl.crawls.{i}.2.{j}.0" in jsondata:
        a = int(jsondata[f"Config.1.Ldl_LASCrawl.crawls.{i}.2.{j}.0"][0])
        b = int(jsondata[f"Config.1.Ldl_LASCrawl.crawls.{i}.2.{j}.1"][0])
        windows.append((a, b))
        j += 1
    crawl_text = jsondata[f"Config.1.Ldl_LASCrawl.crawls.{i}.3"][0]
    crawls.append((start_time, end_time, windows, crawl_text))
    i += 1

print("----------\ni1-crawlEdit v2, the simplicity update\n")

while True:
    cmd = input("\\")
    if cmd == "l":
        for i, item in enumerate(crawls, start=1):
            text = item[3][:15] + "..."
            print(f"{i}: \"{text}\"")
    if cmd.startswith("d"):
        cmd = int(cmd[1:]) - 1
        if 0 <= cmd < len(crawls):
            del crawls[cmd]
    if cmd == "q":
        sys.exit(0)
    if cmd == "s":
        crawl_text = input("Enter Crawl:")
        start_time = input("Enter start epoch or N for now:")
        if start_time == "N":
            start_time = int(epoch)
        else:
            start_time = int(start_time)
            
        end_time = input("Enter expire epoch OR (D) for 24 hours, (W) for a week, (M) for 30 days. |")
        if end_time == "D":
            end_time = start_time + 24*60*60
        elif end_time == "W":
            end_time = start_time + 7*24*60*60
        elif end_time == "M":
            end_time = start_time + 30*24*60*60
        else:
            end_time = int(end_time)
            
        temp = [(0, 23)] # TODO: figure out what the crap this does
        crawl_entry = (start_time, end_time, temp, crawl_text)
        crawls.append(crawl_entry)
    if cmd == "e":
        print("Saving config...")      
        with open('./temp/crawls.py', 'w') as f:
            f.write("d = twc.Data()\n")
            f.write(f"d.serialNum={serialNum}\n")
            f.write("d.crawls=[\n")
            for item in crawls:
                f.write(f"({item[0]}, {item[1]}, {item[2]}, {item[3]!r}),\n")
            f.write("]\n")
            f.write("dsm.set('Config.1.Ldl_LASCrawl', d, 0)\n")
            f.write("dsm.set('Config.1.LASCrawl', d, 0)")
        print("sending config")
        config = configparser.ConfigParser(); config.read('config.ini'); ssh_config = config['SSH']
        ip = ssh_config.get('IP'); port = ssh_config.getint('PORT')
        username = ssh_config.get('USERNAME'); password = ssh_config.get('PASSWORD')
        ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=port, username=username, password=password); sftp = ssh.open_sftp()

        sftp.put("./temp/crawls.py","/home/dgadmin/config/crawls.py")
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("su -l dgadmin -c 'runomni /twc/util/loadSCMTconfig.pyc /home/dgadmin/config/crawls.py'")
        time.sleep(2)
        sftp.close(); ssh.close()
        print("complete?")
        sys.exit(0)
