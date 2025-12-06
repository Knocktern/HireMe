
# HireMe - Hire faster, smarter and Unified

# Never commit on the master branch


## Installation & Setup

### 1. Prerequisites
```bash
# Python 3.7+
# MySQL Server running
# pip package manager
```

### 2. Install Dependencies
```bash
pip install flask flask-sqlalchemy pymysql werkzeug
```

### 3. Database connection
```python

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:<your password>@localhost:3306/job_matching_system'
```

**Note**: The database schema must already exist from running `PROJECT/main.py`

### 4. Run the Application
```bash
python main.py
```


## Project Structure

```
New Project/
├── main.py                    # Phase 1 Flask application
├── templates/
│   ├── base.html              
│   ├── index.html             
│   ├── other template files 
│  
│ 
└── static/
    ├── css/                   
    └── js/                    
```


## Tech Stack

### Frontend
- **CSS Framework**: Tailwind CSS (via CDN)
- **Interactivity**: Alpine.js for state management
- **HTMX**: For dynamic content loading

### Backend
- **Framework**: Flask 2.x
- **Database**: MySQL with PyMySQL connector
- **ORM**: SQLAlchemy
- **Auth**: Werkzeug password hashing
