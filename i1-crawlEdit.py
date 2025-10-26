print("i1-crawlEdit (C) 2025 9D Crew\nConnecting to i1...")
import paramiko; import configparser; import ast; import sys; import time

config = configparser.ConfigParser(); config.read('config.ini'); ssh_config = config['SSH']
ip = ssh_config.get('IP'); port = ssh_config.getint('PORT')
username = ssh_config.get('USERNAME'); password = ssh_config.get('PASSWORD')
ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=ip, port=port, username=username, password=password); sftp = ssh.open_sftp()

stdin, stdout, stderr = ssh.exec_command("perl -e 'print time, \"\\n\";'")
epoch = stdout.read().decode().strip()

print("Loading config...")
sftp.get("/home/dgadmin/config/current/config.py", "./config.py")
sftp.close(); ssh.close()

print("Loading crawls...")

with open("config.py") as file:
    code = file.read()
tree = ast.parse(code)
crawls = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr == "crawls":
                crawls = ast.literal_eval(node.value)
                break

print("--------------------\ni1-crawlEdit v1\n")

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
        dcrawlsidx = code.index("d.crawls")
        dcrawlsidx2 = code.index("]\n", dcrawlsidx)
        dcrawls = code[dcrawlsidx:(dcrawlsidx2+1)]

        newdcrawls = "d.crawls = [\n"
        for crawl in crawls:
            newdcrawls += f"    {str(crawl)},\n"
        newdcrawls += "]"
        
        code = code.replace(dcrawls, newdcrawls, 1)
        with open("config.py", "w") as f:
            f.write(code)
        # push config to i1
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=port, username=username, password=password)
        sftp = ssh.open_sftp()
        sftp.put("config.py", "/home/dgadmin/config/current/config.py")
        sftp.close()
        shell = ssh.invoke_shell()
        shell.send("su -l dgadmin\n"); time.sleep(1)
        shell.send("runomni /twc/util/loadSCMTconfig.pyc /home/dgadmin/config/current/config.py\n"); time.sleep(2)
        ssh.close()
        print("Config Saved!")
        sys.exit(0)