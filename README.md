# Odoo Password Reset Script

A simple Python script to reset user passwords in Odoo by directly updating the PostgreSQL database.

## Setup

1. **Install dependencies:**
   ```bash
   pip install psycopg2-binary passlib python-dotenv
   ```

2. **Create `.env` file:**
   ```env
   DB_HOST=your_database_host
   DB_PORT=5432
   DB_USER=your_db_username
   DB_PASSWORD=your_db_password
   USER_ID=user_id_to_reset
   NEW_PASSWORD=new_password_here
   ```

## Usage

```bash
python reset_odoo_password.py --db your_database_name
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST` | PostgreSQL server hostname |
| `DB_PORT` | PostgreSQL server port |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `USER_ID` | Odoo user ID to reset |
| `NEW_PASSWORD` | New password to set |

## Security Notes

- Uses PBKDF2 SHA512 hashing (60,000 rounds)
- Ensure proper database access permissions

## Requirements

- Python 3.x
- PostgreSQL access to Odoo database
- Required packages: `psycopg2`, `passlib`, `python-dotenv` 