#!/bin/bash
pdf_dir="."     
report_dir="."
script_dir="/usr/lib/pdforganizer/organizer.py"
correctness=""

print_format() {
    echo "Usage: OrganizePDF.sh [options]"
    echo "Options:"
    echo "  -d <PDF Directory> Takes current directory by default"
    echo "  -r <Report Directory> Takes current directory by default"
    echo "  -c Enables correctness score generation"
}

while getopts 'd:r:c' OPTION; do
    case "${OPTION}" in 
        d) 
            pdf_dir="${OPTARG}"
            ;;
        r)
            report_dir="${OPTARG}"
            ;;
        c)
            correctness="1"
            ;;
        *) 
            print_format
            exit 1 ;;
    esac
done


python "$script_dir" "$pdf_dir" "$report_dir" "$correctness"

