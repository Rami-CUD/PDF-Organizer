#!/bin/bash
pdf_dir="."     
report_dir="."
while getopts 'd:r:' OPTION; do
    case "${OPTION}" in 
        d) 
            pdf_dir="${OPTARG}"
            ;;
        r)
            report_dir="${OPTARG}"
            ;;
        *) echo "Bad >:("
        ;;
    esac
done


python organizer.py "$pdf_dir" "$report_dir"

