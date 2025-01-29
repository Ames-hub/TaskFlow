from datetime import datetime
import requests
import zipfile
import hashlib
import shutil
import io
import os
import re

repo_url = 'https://github.com/Ames-hub/TaskFlow.git'
repo_name = re.search(r'/([^/]+)\.git$', repo_url).group(1)
temp_dir = os.path.join(os.getcwd(), 'temp', repo_name)  # temp/<repo_name>

delete_only = [
    'requirements.txt',
    'main.py',
    'README.md',
    'LICENSE',
    '.gitignore',
    'library',
    'logs',
    'cogs',
]

class update_service:
    @staticmethod
    def clone_repository(repo_url=repo_url, destination_folder='temp'):
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
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(destination_folder)
            print(f"Repository cloned to {destination_folder}")
        elif response.status_code == 403:
            print("GitHub API rate limit reached. Try again later.")
            return
        else:
            print(f"Failed to download repository. HTTP Status: {response.status_code}")

    @staticmethod
    def determine_is_modern(delete_clone:bool=True) -> bool:
        """
        Determines if the current version of the bot is the most recent version.
        :return: True if the current version is the most recent, False otherwise.
        """
        did_clone = False
        if not os.path.exists(temp_dir):
            update_service.clone_repository()
            did_clone = True

        for item in delete_only:
            temp_item_hash = update_service.hash(os.path.join(temp_dir, item))
            current_item_hash = update_service.hash(os.path.join(os.getcwd(), item))

            if temp_item_hash is None or current_item_hash != temp_item_hash:
                return False

        if did_clone:
            if delete_clone:
                shutil.rmtree(temp_dir, ignore_errors=True)

        return True

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
        print("Running update... (1/7)")

        # Makes a backup of what's currently in the project root directory
        backup_dir = os.path.join(f'{os.getcwd()}', 'autobackup', f'{datetime.now()}')
        os.makedirs(backup_dir, exist_ok=True)
        for item in os.listdir():
            if item != 'autobackup':
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_dir, item))
                else:
                    shutil.copy(item, os.path.join(backup_dir, item))

        print("Backed up current version to './autobackup' (2/7)")

        shutil.rmtree(temp_dir, ignore_errors=True)
        if not os.path.exists(temp_dir):
            print("Cloning repository to temp directory... (3/7)")
            update_service.clone_repository(repo_url, temp_dir)
            if not os.path.exists(temp_dir):
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
        for item in os.listdir(temp_dir):
            shutil.move(
                src=os.path.join(temp_dir, item),
                dst=os.path.join(os.getcwd(), item),
            )

        # Clean up the temp folder
        print("Cleaned up temp folder (6/7)")
        shutil.rmtree('temp', ignore_errors=True)
        # shutil.rmtree(repo_name, ignore_errors=True)
        print("Updated files (7/7)")

        print("Update complete! Please restart the bot.")