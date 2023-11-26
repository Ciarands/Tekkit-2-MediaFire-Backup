# Tekkit-2 automated backup
Script which compresses and uploads Tekkit 2 server backups to MediaFire, posting webhooks to discord.

### Prerequisites
- git
- python3
- mediafire account
- basic familiarity with systemctl (if creating a service)

### Installation
Download the project & install requirements

```git clone https://github.com/Ciarands/Tekkit-2-MediaFire-Backup.git```

```cd Tekkit-2-MediaFire-Backup && python3 -m pip install -r requirements.txt```

Create data.json (data.example.json for reference)

```json
{
    "email": "user@email.com",
    "password": "**************",
    "webhook": "https://canary.discord.com/api/webhooks/**********/***********",
    "app_id": "",
    "folder_key": "",
    "working_dir": "/home/opc/Tekkit/backups/world"
}
```

Setup auto-backup.service as a service (template below)
```service
[Unit]
Description=Tekkit 2 server backups to MediaFire
After=syslog.target

[Service]
Type=simple
User=tekkit
WorkingDirectory=/home/opc/Tekkit/
ExecStart=/bin/bash -lc 'python3 backup.py'

[Install]
WantedBy=multi-user.target
```

### Contact
discord - `ciaran_ds`
