from datetime import datetime
import requests
import zipfile
import shutil
import io
import os

repo_url = 'https://github.com/Ames-hub/TaskFlow.git'

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
        else:
            print(f"Failed to download repository. HTTP Status: {response.status_code}")

    @staticmethod
    def run_update():
        print("Running update... (1/9)")

        # Makes a backup of what's currently in the project root directory
        backup_dir = os.path.join(f'{os.getcwd()}', 'autobackup', f'{datetime.now()}')
        os.makedirs(backup_dir, exist_ok=True)
        for item in os.listdir():
            if item != 'autobackup':
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_dir, item))
                else:
                    shutil.copy(item, os.path.join(backup_dir, item))

        print("Backed up current version to './autobackup' (2/9)")

        # Ensure the temp folder exists (with the repository contents)
        while True:  # retry logic
            if not os.path.exists('temp'):
                print("Cloning repository to temp directory... (3/9)")
                update_service.clone_repository(repo_url, 'temp')
                if not os.path.exists('temp'):
                    print("Failed to clone repository")
                    return
                break
            else:
                shutil.rmtree('temp', ignore_errors=True)
                continue

        # Deletes all folders in proj root directory except for temp, logs, .git and secrets.env
        for item in os.listdir():
            for exemption in ['temp', 'logs', '.git', '.env', 'venv', 'data', 'autobackup']:
                if exemption in item or item.startswith('.'):  # Ignore hidden files
                    print(f"Item '{item}' is exempted (4/9)")
                    break
            else:
                if os.path.isdir(item):
                    shutil.rmtree(item, ignore_errors=True)
                    print(f"Removed folder '{item}' (5/9)")
                else:
                    os.remove(item)
                    print(f"Removed file '{item}' (6/9)")

        print("Removed all old files (7/9)")

        # Move the contents of the temp folder to the project root
        tempdir = os.path.join(os.getcwd(), 'temp', os.listdir('temp')[0])  # temp/<repo_name>
        for item in os.listdir(tempdir):
            shutil.move(os.path.join(tempdir, item), os.path.join(os.getcwd(), item))

        # Clean up the temp folder
        shutil.rmtree('temp', ignore_errors=True)
        print("Cleaned up temp folder (8/9)")
        print("Updated files (9/9)")

        print("Update complete! Please restart the bot.")