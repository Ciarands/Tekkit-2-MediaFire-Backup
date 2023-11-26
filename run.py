import json
import time
import zipfile
import requests

from pathlib import Path
from mediafire import MediaFireApi
from mediafire import MediaFireUploader

class BackupFiles:
    def __init__(self, **kwargs) -> None:
        self.api = MediaFireApi()
        self.uploader = MediaFireUploader(self.api)
        self.session = self.api.user_get_session_token(
            email=kwargs.get("email"),
            password=kwargs.get("password"),
            app_id=kwargs.get("app_id"))
        
        self.api.session = self.session
        self.webhook = kwargs.get("webhook")
        self.upload_folder = kwargs.get("folder_key")
        self.working_dir = kwargs.get("working_dir")
        print(self.working_dir)

        self.file_path = Path(f"{self.working_dir}/Last")
        self.send_webhook("Server Online :3", "auto-backup.service started!", 0x00ff00, {"name": "Server Status", "value": "`active (running)`"})
        
    def send_webhook(self, title: str, description: str, colour: int, field: dict) -> None:
        """Send webhook to Discord channel"""
        if not self.webhook:
            return

        print("Sending webhook...")
        data = {
            "content": "@here",
            "embeds": [
                {
                    "type": "rich",
                    "title": title,
                    "description": description,
                    "color": colour,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                    "fields": [field]
                }
            ]
        }

        requests.post(self.webhook, json=data)
        print("Webhook sent")

    def upload(self, file_dir: Path) -> dict:
        """API call to upload file to MediaFire"""
        with open(file_dir, "rb") as file:
            result = self.uploader.upload(file, file_dir.name, folder_key=self.upload_folder)
        
        if not result:
            self.send_webhook("Error :(", "Something went wrong when retrieving latest backup folder", 0xff0000, {"name": "MediaFireApiError", "value": "No result found for upload API call"})
            raise Exception("No result found for upload API call")

        return result
    
    def get_file_url(self, file_key: str) -> str:
        """API call to get download link for file"""
        response = self.api.file_get_links(quick_key=file_key, link_type="normal_download")
        if not response:
            self.send_webhook("Error :(", "Something went wrong when retrieving latest backup folder", 0xff0000, {"name": "MediaFireApiError", "value": "No response found for file_get_links API call"})
            raise Exception("No response found for file_get_links API call")
        
        links = response.get("links", {})
        if not links:
            self.send_webhook("Error :(", "Something went wrong when retrieving latest backup folder", 0xff0000, {"name": "MediaFireApiError", "value": "No links found in response"})
            raise Exception("No links found in response")
        
        return links[0].get("normal_download")
    
    def get_uploaded_files(self) -> list:
        """API call to get list of files in upload folder"""
        response = self.api.folder_get_content(folder_key=self.upload_folder, content_type="files")
        if not response:
            self.send_webhook("Error :(", "Something went wrong when retrieving latest backup folder", 0xff0000, {"name": "MediaFireApiError", "value": "No response found for folder_get_content API call"})
            raise Exception("No response found for folder_get_content API call")
        
        folder_content = response.get("folder_content", {}).get("files", {})
        if not folder_content:
            print("No files found in folder!")
            return []
        
        return [file.get("filename") for file in folder_content]

    def get_latest_backup_folder(self) -> Path:
        """Fetch latest backup folder from set working directory"""
        with open(self.file_path, "r") as f:
            file_name = f.read()

        backup_folder = Path(f"{self.working_dir}/{file_name}")
        if backup_folder.exists():
            return backup_folder
        else:
            self.send_webhook("Error :(", "Something went wrong when retrieving latest backup folder", 0xff0000, {"name": "FileNotFoundError", "value": f"File `{backup_folder}` not found"})
            raise FileNotFoundError(f"File {backup_folder} not found")
        
    def wait_for_file_update(self) -> float:
        last_modified = self.file_path.stat().st_mtime
        while True:
            time.sleep(1)
            if self.file_path.stat().st_mtime == last_modified:
                continue
            last_modified = self.file_path.stat().st_mtime
            return last_modified
        
    def zip_folder(self, folder) -> Path:
        """Compress folder into zip file and return path"""
        with zipfile.ZipFile(f"{folder}.zip", "w", zipfile.ZIP_DEFLATED) as zip:
            for file in folder.iterdir():
                zip.write(file, file.name)

        return Path(f"{folder}.zip")
    
    def delete_zip(self, zip_path: Path) -> None:
        """Delete zip file"""
        zip_path.unlink()
        
    def main(self) -> None:
        backup_folder = self.get_latest_backup_folder()
        if f"{backup_folder.name}.zip" in self.get_uploaded_files():
            print(f"File {backup_folder.name}.zip already uploaded")
            self.wait_for_file_update()
            return

        zip_path = self.zip_folder(backup_folder)
        print(f"Uploading {zip_path.name}...")

        result = self.upload(zip_path)
        if not result:
            self.send_webhook("Error :(", "Something went wrong when uploading to MediaFire", 0xff0000, {"name": "Exception", "value": "No result returned from upload"})
            raise Exception("No result returned from upload")
        
        url = self.get_file_url(result.quickkey)
        if not url:
            self.send_webhook("Error :(", "Something went wrong when uploading to MediaFire", 0xff0000, {"name": "Exception", "value": "No download URL returned from API"})
            raise Exception("No download URL returned from API")

        print("Cleaning up...")
        self.delete_zip(zip_path)
        self.send_webhook("New Backup :D", "Uploaded backup to MediaFire successfully!", 0x00ff00, {"name": "MediaFire Download", "value": f"[`{zip_path.name}`]({url} \"MediaFire Download\")"})

        new_backup_timestamp = self.wait_for_file_update()
        print(f"New backup detected at {time.strftime('%H:%M:%S', time.gmtime(new_backup_timestamp))}")
        
if __name__ == "__main__":
    with open("data.json", "r") as f:
        data = json.load(f)

    bf = BackupFiles(
        email=data.get("email"),
        password=data.get("password"),
        webhook=data.get("webhook"),
        app_id=data.get("app_id"),
        folder_key=data.get("folder_key"),
        working_dir=data.get("working_dir")
    )

    while True:
        bf.main()
