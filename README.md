# MaintenePro CMMS
### Industrial Computerized Maintenance Management System
Built with: Django · SQLite · HTML/CSS

---

## Requirements
- Python 3.10 or newer
- pip

---

## Installation Steps (Windows)

### 1. Install Python
Download from https://www.python.org/downloads/
During install: check "Add Python to PATH"

### 2. Open Command Prompt (CMD)
Press Win+R → type cmd → Enter

### 3. Go to the project folder
```
cd C:\path\to\cmms
```

### 4. Install Django
```
pip install -r requirements.txt
```

### 5. Setup the database + demo data
```
python setup.py
```

### 6. Start the server
```
python manage.py runserver
```

### 7. Open your browser
```
http://127.0.0.1:8000
```

Login: **admin** / **admin123**

---

## Installation Steps (Linux / Ubuntu)

```bash
cd /path/to/cmms
pip3 install -r requirements.txt
python3 setup.py
python3 manage.py runserver
```

---

## Features
- **Dashboard** — KPIs, recent WOs, upcoming PM tasks
- **Assets** — Full equipment registry with search & filter
- **Work Orders** — Create, assign, track, close maintenance jobs
- **PM Schedule** — Preventive maintenance with auto-reschedule
- **Reports** — Status charts, category breakdown, monthly trends
- **Spare Parts** — Track parts used per work order with costs
- **Admin Panel** — Full database management at /admin/

---

## Adding More Users

1. Go to http://127.0.0.1:8000/admin/
2. Login with admin / admin123
3. Click Users → Add User
4. Set username, password, and permissions

---

## Project Structure
```
cmms/
├── manage.py           ← Django management tool
├── setup.py            ← Run ONCE to setup database
├── requirements.txt    ← Python packages needed
├── cmms.db             ← SQLite database (created on setup)
├── cmms/
│   ├── settings.py     ← Configuration
│   └── urls.py         ← Main URL routing
└── maintenance/
    ├── models.py       ← Database models
    ├── views.py        ← Business logic
    ├── forms.py        ← HTML forms
    ├── urls.py         ← App URL routing
    ├── admin.py        ← Admin panel config
    └── templates/
        └── maintenance/
            ├── base.html
            ├── dashboard.html
            ├── asset_list.html
            ├── asset_detail.html
            ├── asset_form.html
            ├── wo_list.html
            ├── wo_detail.html
            ├── wo_form.html
            ├── pm_list.html
            ├── pm_form.html
            ├── reports.html
            └── login.html
```

---

## To Run on Your Local Network (Other Devices Can Access)
```
python manage.py runserver 0.0.0.0:8000
```
Then access from any device on same WiFi: http://YOUR-PC-IP:8000

---

## Backup Your Data
The entire database is one file: `cmms.db`
Copy it to backup. To restore, replace the file.

---

Built for industrial maintenance professionals — Egypt 🇪🇬
