# PDF-Organizer
## Installation
Grab the .deb file from the latest release through any method.
### Example:
```sh
wget https://github.com/Rami-CUD/PDF-Organizer/releases/download/1.0.3/PDFOrganizer.deb
```
Then apt install the .deb file.
```sh
sudo apt install ./PDFOrganizer.deb
```
## Usage 
OrganizePDF.sh [options]
### Options:
- -d <PDF Directory> Takes current directory by default
- -r <Report Directory> Takes current directory by default
- -c Enables correctness score generation

### Example:
```sh
OrganizePDF.sh -c
```
*Runs the script in the current directory with correctness score generation enabled*
