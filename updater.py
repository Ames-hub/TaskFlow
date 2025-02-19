from datetime import datetime, timedelta
import requests
import hashlib
import shutil
import os
import re

repo_url = 'https://github.com/Ames-hub/TaskFlow.git'
repo_name = f"{re.search(r'/([^/]+)\.git$', repo_url).group(1)}-main"
repo_clone_dir = os.path.join(os.getcwd(), repo_name)  # temp/<repo_name>
backup_dir = os.path.join(f'{os.getcwd()}', 'autobackup')

delete_only = [
    'requirements.txt',
    'main.py',
    'README.md',
    'LICENSE',
    'library',
    'cogs',
]

class update_service:
    @staticmethod
    def clone_repository(repo_url=repo_url, destination_folder=repo_clone_dir):
        # Convert GitHub URL to the zip download URL
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        if "github.com" in repo_url:
            repo_url += "/archive/refs/heads/main.zip"
        else:
            raise ValueError("Only GitHub repositories are supported with this method.")

        # Fetch the repository zip file
        retries = 0
        while True:
            try:
                response = requests.get(repo_url)
                break
            except requests.exceptions.ConnectionError:
                retries += 1
                if retries >= 3:
                    print("Couldn't connect to GitHub. Exiting...")
                    return
                print("Failed to connect to GitHub. Retrying...")

        if response.status_code == 200:
            print("Downloading repository...")
            # Unzip the contents
            extracted_folder = os.path.join(destination_folder, repo_name)  # Actual extracted path
            if not os.path.exists(extracted_folder):
                print("Failed to extract repository")
                return

            for item in os.listdir(extracted_folder):
                shutil.move(os.path.join(extracted_folder, item), os.getcwd())
            print(f"Repository cloned to {destination_folder}")
        elif response.status_code == 403:
            print("GitHub API rate limit reached. Try again later.")
            return
        else:
            print(f"Failed to download repository. HTTP Status: {response.status_code}")

    @staticmethod
    def delete_old_backups() -> int:
        """
        Finds backups of date older than 7 days and deletes them when the number of backups exceeds 5.
        :return:
        """
        if not os.path.exists(backup_dir):
            return 0
        dir_list = os.listdir(backup_dir)
        if len(dir_list) <= 5:
            return 0

        delete_count = 0
        for item_name in dir_list:
            if datetime.strptime(item_name, "%Y-%m-%d %H:%M:%S") > datetime.now() - timedelta(days=7):
                continue

            item_path = os.path.join(backup_dir, item_name)
            if not os.path.isdir(item_path):
                continue

            shutil.rmtree(item_path, ignore_errors=True)
            delete_count += 1
            continue

        return delete_count

    @staticmethod
    def determine_is_modern() -> bool:
        """
        Determines if the current version of the bot is the most recent version.
        :return: True if the current version is the most recent, False otherwise.
        """
        latest_ver = update_service.get_latest_ver()

        rdc = rd_config()
        data = rdc.read_cfg()

        current_ver = f"{data['v_major']}.{data['v_minor']}.{data['v_patch']}"

        print(f"Latest version: {latest_ver}")
        print(f"Current version: {current_ver}")
        return latest_ver == current_ver

    @staticmethod
    def get_latest_ver():
        # Change this should you have your own instance of RD running. Uses this to get the version (M.M.P.) of the bot.
        UPDATE_SERVER_URL = os.environ.get('UPDATE_SERVER_URL', 'http://127.0.0.1:4096')

        # Fetches the version of the bot from the update server
        response = requests.post(
            url=f"{UPDATE_SERVER_URL}/api/vcs/getversion",
            json={
                "repo_owner": os.environ.get('UPDATE_SERVER_USERNAME', 'Ames-hub'),
                "repo_name": "TaskFlow",
            },
            headers={
                "Content-Type": "application/json",
            }
        )

        json = response.json()['version']
        latest_ver = f"{json['major']}.{json['minor']}.{json['patch']}"
        return latest_ver

    @staticmethod
    def hash(path: str) -> str | None:
        """Hashes a file or a folder. Returns a SHA-256 hash."""
        if os.path.isfile(path):
            return update_service.hash_file(path)
        elif os.path.isdir(path):
            return update_service.hash_folder(path)
        else:
            print(f"Warning: Path '{path}' does not exist.")
            return None

    @staticmethod
    def hash_file(file_path: str) -> str:
        """Hashes a file using SHA-256."""
        if not os.path.exists(file_path):
            print(f"Warning: File '{file_path}' not found, skipping hash.")
            return ""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def hash_folder(folder_path: str) -> str:
        """Recursively hashes a folder by hashing all files and combining their hashes."""
        hasher = hashlib.sha256()
        for root, _, files in sorted(os.walk(folder_path)):
            for file in sorted(files):
                file_path = os.path.join(root, file).replace("\\", "/")  # Normalize
                hasher.update(update_service.hash_file(file_path).encode())
        return hasher.hexdigest()

    @staticmethod
    def run_update():
        """
        Updates the bot to the latest version.
        :return:
        """
        if update_service.determine_is_modern():
            print("Bot is already up to date.")

        print("Checking for old backups and deleting them...")
        del_count = update_service.delete_old_backups()
        print(f"Deleted {del_count} old backups.")

        print("Running update... (1/7)")

        # Makes a backup of what's currently in the project root directory
        current_backup_dir = os.path.join(backup_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.makedirs(current_backup_dir, exist_ok=True)
        for item in os.listdir():
            if item != 'autobackup':
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(current_backup_dir, item))
                else:
                    shutil.copy(item, os.path.join(current_backup_dir, item))

        print("Backed up current version to './autobackup' (2/7)")

        shutil.rmtree(repo_clone_dir, ignore_errors=True)
        if not os.path.exists(repo_clone_dir):
            print("Cloning repository to temp directory... (3/7)")
            update_service.clone_repository()
            if not os.path.exists(repo_clone_dir):
                print("Failed to clone repository")
                return

        # Deletes all folders in proj root directory except for temp, logs, .git and secrets.env
        for item in os.listdir():
            for del_item in delete_only:
                if del_item not in item or item.startswith('.'):  # Ignore hidden files
                    print(f"Item '{item}' is exempted (4/7)")
                    break
            else:
                if os.path.isdir(item):
                    shutil.rmtree(item, ignore_errors=True)
                    print(f"Removed folder '{item}' (4/7)")
                else:
                    os.remove(item)
                    print(f"Removed file '{item}' (4/7)")

        print("Removed all old files (5/7)")

        # Move the contents of the temp folder to the project root
        for item in os.listdir(repo_clone_dir):
            if item == repo_name:
                continue
            shutil.move(
                src=os.path.join(repo_clone_dir, item),
                dst=os.path.join(os.getcwd(), item),
            )

        # Clean up the temp folder
        print("Cleaned up temp folder (6/7)")
        shutil.rmtree(repo_clone_dir, ignore_errors=True)

        # Update the saved version in the RDC file
        rdc = rd_config()
        latest = update_service.get_latest_ver()
        rdc.update('v_major', latest.split('.')[0])
        rdc.update('v_minor', latest.split('.')[1])
        rdc.update('v_patch', latest.split('.')[2])
        print("Updated saved version (7/7)")

        print("Update complete! Please restart the bot.")

class rd_config:
    """
    Raindrop Configuration System for a repository.
    Manages the entire .rdc directory within a repository and its contents.
    """
    def __init__(self):
        self.rdc_file = None

    def read_cfg(self) -> dict:
        """
        Read the RDC file for a repository.

        :return:
        """
        self.rdc_file = f'.rdc/cfg'
        with open(self.rdc_file, 'r') as f:
            data = f.read()

        # Parse the data
        line_list = data.split('\n')
        rdc_dict = {}
        for line in line_list:
            if len(line) <= 0:
                continue
            try:
                key, value = line.split("=", maxsplit=1)
            except ValueError:
                print(f"Error parsing line in RDC read func: {line}")
                continue

            # Parse back the description
            rdc_dict[key] = value.replace("<br>", "\n")

        return rdc_dict

    def update(self, key, value):
        """
        Update a key in the RDC file.

        :param key: The key to update
        :param value: The value to update the key to
        :return:
        """
        if self.rdc_file is None:
            self.rdc_file = f'.rdc/cfg'

        if not os.path.exists(self.rdc_file):
            raise

        with open(self.rdc_file, 'r') as f:
            data = f.read()

        # Parse the data
        line_list = data.split('\n')
        rdc_dict = {}
        for line in line_list:
            if len(line) <= 0:
                continue
            try:
                k, v = line.split("=", maxsplit=1)
            except ValueError:
                print(f"Error parsing in RDC update func. Line: {line}")
                continue
            rdc_dict[k] = v

        rdc_dict[key] = value

        with open(self.rdc_file, 'w') as f:
            f.write(f"owner={rdc_dict['owner']}\n")
            f.write(f"name={rdc_dict['name']}\n")
            f.write(f"description={rdc_dict['description']}\n")
            f.write(f"uuid={rdc_dict['uuid']}\n")
            f.write(f"visibility={rdc_dict['visibility']}\n")
            f.write(f"created_at={rdc_dict['created_at']}\n")
            f.write(f"last_update_at={datetime.now()}\n")
            f.write(f"v_major={rdc_dict['v_major']}\n")
            f.write(f"v_minor={rdc_dict['v_minor']}\n")
            f.write(f"v_patch={rdc_dict['v_patch']}\n")

        return True