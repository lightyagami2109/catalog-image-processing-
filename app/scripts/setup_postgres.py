"""Python script to setup PostgreSQL database (alternative to bash script)."""
import os
import sys
import asyncio
import asyncpg
from getpass import getpass

# Default values
DB_NAME = os.getenv("DB_NAME", "catalogdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", None)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))


async def setup_database():
    """Create database if it doesn't exist."""
    print("Setting up PostgreSQL database for Catalog Image Pipeline...")
    print()
    print("Database configuration:")
    print(f"  Name: {DB_NAME}")
    print(f"  User: {DB_USER}")
    print(f"  Host: {DB_HOST}")
    print(f"  Port: {DB_PORT}")
    print()
    
    # Get password if not set
    password = DB_PASSWORD
    if not password:
        password = getpass(f"Enter PostgreSQL password for user '{DB_USER}': ")
    
    try:
        # Connect to postgres database to create our database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=password,
            database="postgres"  # Connect to default postgres DB
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )
        
        if not exists:
            # Create database
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"✓ Database '{DB_NAME}' created successfully!")
        else:
            print(f"✓ Database '{DB_NAME}' already exists.")
        
        await conn.close()
        
        # Now initialize tables in the new database
        print()
        print("Initializing database tables...")
        
        # Set DATABASE_URL for init_db
        database_url = f"postgresql+asyncpg://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        os.environ["DATABASE_URL"] = database_url
        
        # Import and run init_db
        from app.db import init_db
        await init_db()
        
        print()
        print("✓ Setup complete!")
        print()
        print("Add this to your .env file:")
        print(f"DATABASE_URL={database_url}")
        print()
        print("⚠️  Note: Password is shown above. Keep your .env file secure!")
        
    except asyncpg.InvalidPasswordError:
        print("✗ Error: Invalid password")
        sys.exit(1)
    except asyncpg.InvalidCatalogNameError:
        print(f"✗ Error: User '{DB_USER}' does not exist or cannot connect")
        print("  Make sure PostgreSQL is running and user exists")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_database())

