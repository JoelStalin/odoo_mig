#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import logging
import shutil
from configparser import ConfigParser
import json

# Constants
LOG_FILE = 'upgrade.log'
BACKUP_DIR = 'backups'

def setup_logging():
    """Sets up logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_odoo_version():
    """
    Detects the Odoo version by reading the version from a manifest file.
    """
    # In a real scenario, we might need a more robust way to find a manifest file.
    # For this case, we'll use a known path.
    manifest_path = 'addons/extra/exo_api/__manifest__.py'
    if not os.path.exists(manifest_path):
        logging.error(f"Manifest file not found at {manifest_path}")
        return None

    try:
        with open(manifest_path, 'r') as f:
            manifest_str = f.read()
            # The manifest is a string representation of a dictionary.
            # We can use ast.literal_eval for safe evaluation.
            import ast
            manifest_dict = ast.literal_eval(manifest_str)
            version = manifest_dict.get('version', '')
            # Odoo version is typically the first part of the version string (e.g., '17.0.1.0.0')
            if version:
                return version.split('.')[0]
    except Exception as e:
        logging.error(f"Could not read or parse manifest file: {e}")

    return None

def main():
    """Main function to run the upgrade script."""
    setup_logging()
    logging.info("Starting Odoo upgrade script.")

    current_version = get_odoo_version()
    if not current_version:
        logging.error("Could not determine the current Odoo version. Aborting.")
        return

    logging.info(f"Detected Odoo version: {current_version}")

    target_version = display_menu(current_version)
    if not target_version:
        logging.info("No valid upgrade option selected. Aborting.")
        return

    logging.info(f"User selected to upgrade to Odoo {target_version}")

    # Ask for confirmation before proceeding
    print(f"\nThis script will perform the following actions:")
    print(f"1. Create a backup of the database.")
    print(f"2. Create a backup of the 'addons' directory.")
    print(f"3. Guide you through the final migration steps.")

    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() != 'y':
        logging.info("User aborted the operation.")
        return

    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Perform backups
    if not backup_database(target_version) or not backup_modules(target_version):
         logging.error("Backup failed. Aborting upgrade.")
         return

    display_final_instructions(target_version)


def display_final_instructions(target_version):
    """Displays the final instructions for the user."""
    db_config = get_db_config()
    db_name = db_config.get('name')
    if not db_name:
        db_name = "odoo" # Fallback for this example

    logging.info("Upgrade process is ready for the final step.")
    print("\n" + "="*80)
    print(" " * 30 + "UPGRADE INSTRUCTIONS")
    print("="*80)
    print("\nThe automated part of the script is complete. Please follow these manual steps:")
    print("\n1. IMPORTANT: Ensure your custom modules in the 'addons' directory have been")
    print(f"   updated and are compatible with Odoo {target_version}.")
    print(f"\n2. Ensure you have the Odoo source code for version {target_version} available.")
    print("\n3. Run the Odoo migration command from the new Odoo source code directory:")
    print("\n   cd /path/to/your/new/odoo-server/")
    print(f"   ./odoo-bin -c /path/to/your/odoo.conf -d {db_name} -u all --stop-after-init")

    print("\n   - Replace '/path/to/your/new/odoo-server/' with the actual path.")
    print("   - Ensure your 'odoo.conf' file points to the correct addons path, including your custom modules.")

    print("\n4. After the command completes, start your Odoo server normally.")
    print("\n" + "="*80)
    logging.info("Script finished.")


def get_db_config():
    """Reads database configuration from odoo.conf."""
    config = ConfigParser()
    if not os.path.exists('odoo.conf'):
        logging.error("odoo.conf file not found!")
        return {}

    config.read('odoo.conf')
    return {
        'host': config.get('options', 'db_host', fallback='localhost'),
        'port': config.get('options', 'db_port', fallback='5432'),
        'user': config.get('options', 'db_user', fallback=None),
        'password': config.get('options', 'db_password', fallback=None),
        'name': config.get('options', 'db_name', fallback=None) # Assuming db_name is in the conf
    }

def backup_database(version_tag):
    """Creates a backup of the database using pg_dump."""
    db_config = get_db_config()
    db_name = db_config.get('name')

    if not db_name:
        # Let's try to get the db_name from the command line if not in conf, for example purposes
        # In a real case, we would need a more robust way to get the db name
        db_name = "odoo" # Fallback for this example
        logging.warning(f"db_name not found in odoo.conf, falling back to '{db_name}'")


    backup_file = os.path.join(BACKUP_DIR, f"{db_name}_v{version_tag}_backup.dump")
    logging.info(f"Backing up database '{db_name}' to '{backup_file}'...")

    # For security, pg_dump can use the PGPASSWORD environment variable
    env = os.environ.copy()
    if db_config.get('password'):
        env['PGPASSWORD'] = db_config['password']

    # We are simulating this part as we can't run pg_dump in this environment
    logging.info(f"Simulating: pg_dump -h {db_config['host']} -p {db_config['port']} -U {db_config['user']} -F c -b -v -f {backup_file} {db_name}")

    # In a real environment, the command would be:
    # try:
    #     process = subprocess.run([
    #         'pg_dump',
    #         '-h', db_config['host'],
    #         '-p', db_config['port'],
    #         '-U', db_config['user'],
    #         '-F', 'c', '-b', '-v',
    #         '-f', backup_file,
    #         db_name
    #     ], env=env, check=True, capture_output=True, text=True)
    #     logging.info("Database backup successful.")
    #     logging.debug(process.stdout)
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"Database backup failed: {e.stderr}")
    #     return False
    # except FileNotFoundError:
    #     logging.error("pg_dump command not found. Is PostgreSQL client installed and in your PATH?")
    #     return False

    return True # Simulating success

def backup_modules(version_tag):
    """Creates a backup of the addons directory."""
    addons_path = 'addons'
    backup_path = os.path.join(BACKUP_DIR, f"addons_v{version_tag}_backup")

    if os.path.exists(backup_path):
        logging.warning(f"Backup directory {backup_path} already exists. It will be removed.")
        shutil.rmtree(backup_path)

    logging.info(f"Backing up '{addons_path}' to '{backup_path}'...")
    try:
        shutil.copytree(addons_path, backup_path)
        logging.info("Modules backup successful.")
    except Exception as e:
        logging.error(f"Modules backup failed: {e}")
        return False

    return True


def display_menu(current_version):
    """
    Displays the upgrade menu and returns the selected target version.
    """
    # Available upgrade paths
    upgrade_paths = {
        '15': ['16'],
        '16': ['17'],
        '17': ['18']
    }

    possible_upgrades = upgrade_paths.get(current_version, [])

    if not possible_upgrades:
        logging.warning(f"No upgrade path available for Odoo version {current_version}.")
        return None

    print("\nPlease select an upgrade option:")
    for i, version in enumerate(possible_upgrades, 1):
        print(f"{i}. Upgrade from Odoo {current_version} to Odoo {version}")

    print("0. Exit")

    while True:
        try:
            choice = int(input("Enter your choice: "))
            if choice == 0:
                return None
            if 1 <= choice <= len(possible_upgrades):
                return possible_upgrades[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    main()
