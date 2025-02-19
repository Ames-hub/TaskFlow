from datetime import datetime
import dotenv
import requests
import shutil
import os

repo_url = 'https://github.com/Ames-hub/TaskFlow.git'
repo_clone_dir = "TaskFlow-main"
backup_dir = os.path.join(f'{os.getcwd()}', 'autobackup')

dotenv.load_dotenv('updater.env')

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
    def determine_is_modern() -> bool:
        """
        Determines if the current version of the bot is the most recent version.
        :return: True if the current version is the most recent, False otherwise.
        """
        latest_ver = update_service.get_latest_ver()
        current_ver = update_service.get_current_ver()

        print(f"Latest version: {latest_ver}")
        print(f"Current version: {current_ver}")
        return latest_ver == current_ver

    @staticmethod
    def get_current_ver():
        rdc = rd_config()
        data = rdc.read_cfg()

        current_ver = f"{data['v_major']}.{data['v_minor']}.{data['v_patch']}"
        return current_ver

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
    def clone_repo():
        """
        Clones the repository to the local machine.
        """
        if os.path.exists(repo_clone_dir):
            shutil.rmtree(repo_clone_dir)

        os.system(f'git clone {repo_url} {repo_clone_dir}')

    @staticmethod
    def delete_old_files():
        """
        Deletes files that are not needed in the new version.
        """
        for file in delete_only:
            if os.path.exists(file):
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)

    @staticmethod
    def move_files():
        """
        Moves the files from the cloned repository to the current directory.
        """
        for file in os.listdir(repo_clone_dir):
            if file in delete_only:
                continue

            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                shutil.move(os.path.join(repo_clone_dir, file), file)

    @staticmethod
    def run_update():
        """
        Runs the update process.
        """
        if not update_service.determine_is_modern():
            print("The bot is not up to date. Updating now...")
        else:
            print("The bot is already up to date.")
            return True

        update_service.clone_repo()
        update_service.delete_old_files()
        update_service.move_files()

        # Update the version number
        rdc = rd_config()
        server_data = update_service.get_latest_ver().split('.')[0]

        rdc.update('v_major', server_data[0])
        rdc.update('v_minor', server_data[1])
        rdc.update('v_patch', server_data[2])

        print("Update complete.")

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