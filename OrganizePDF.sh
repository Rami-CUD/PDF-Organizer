#!/bin/bash
if [ -d "$1" ]; then
    python organizer.py "$1"
else
    echo "Please enter a valid Directory. Format: organize [directory]"
fi
