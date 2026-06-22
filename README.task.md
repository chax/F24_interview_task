# Overview

We want to create a large-scale browser-based file system, functionally similar to Dropbox’s web interface, or a folder browsing structure you might find on a Windows or macOS device. A user should be able to:
 - Create folders and subfolders
 - Create new files in the folders
 - Search files by their exact name within a parent folder or across all files
    List the top 10 files that start with a search string. 
    This will be used in the search box to show possible matches when the user is typing. Only “start with” logic is required.
 - Delete folders and files

For this exercise, you can assume that a file is simply its name and does not contain any other content.

The frontend does NOT have to include any design or be adapted for mobile devices. 
The default React framework is acceptable.
API service should use a SQL or noSQL database ( of your choice! InMemory or File DB is also acceptable).

Provide a README with instructions on how to deploy your application.

Additional notes:
 - Solution has to build and run in debug mode
 - Docker is optional and it will be considered
