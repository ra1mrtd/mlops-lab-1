**Question 1**
uv init created the basic Python project structure. The main files are pyproject.toml, which stores project information and dependencies, python-version, which specifies the Python version, README.md for documentation, and the src folder where the project code is stored.

**Question 2**
After running dvc init, DVC created the .dvc folder and .dvcignore.
The .dvc/config file stores DVC configuration, for example the remote storage settings. The .dvc/.gitignore file prevents DVC internal files from being tracked by Git. The .dvcignore file is similar to .gitignore, but it tells DVC which files or folders it should ignore.
The configuration files should be pushed to Git, but the DVC cache and the actual dataset files should not.

**Question 3**
For this lab I used a local folder as my DVC remote instead of DagsHub, which was one of the allowed options.
If DagsHub is used, the credentials can be stored in DVC configuration with different scopes, such as global or local configuration. Credentials should not be pushed to GitHub because they are private information. Only non-secret configuration should be committed.

**Question 4**
When I ran:
dvc add data
DVC added the data folder to .gitignore.
This means Git will not track the actual dataset files. Instead, DVC tracks the dataset and Git only tracks the small pointer file created by DVC.

**Question 5**
Yes, a file called data.dvc was created.
It contains information about the tracked data folder, such as its hash, size, number of files, and path. It does not contain the actual images. It works like a pointer that tells DVC which version of the dataset should be used.

**Question 6**
On GitHub I can see the source code and the data.dvc pointer file, but I cannot see the actual dataset files because they are not stored in Git.
The actual data is stored in the DVC remote. Since I used a local remote, the data is stored in a separate folder on my computer instead of on DagsHub.

**Question 7**
When I clone the repository into a new folder, the Git files are downloaded, including data.dvc, but the actual data folder is not automatically restored.
To get the dataset, I need to run:
dvc pull
This retrieves the version of the data referenced by the current data.dvc file.

**Question 8**
When I checked out the older commit and then ran:
dvc checkout
the food11_processed and food11_processed_mini folders disappeared because they did not exist in that older version of data.dvc.
After switching back to main and running dvc checkout again, the processed folders came back.
This showed how Git can control the version of the DVC pointer while DVC restores the matching version of the actual data.