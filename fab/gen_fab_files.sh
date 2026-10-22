#!/bin/bash

GERBER_DIR="gerber_and_drill"
GERBER_ZIP="gerber_and_drill.zip"

PLACEMENT_DIR="placement"
PLACEMENT_ZIP="placement.zip"

zip_folder() {
  local source_dir="$1"
  local zip_name="$2"

  if [ ! -d "$source_dir" ]; then
    echo "Error: directory '$source_dir' does not exist."
    exit 1
  fi

  cd "$source_dir" || exit 1

  # Remove the previous ZIP with the same name, if it exists
  rm -f "$zip_name"

  # Create the ZIP inside the folder,
  # including everything inside it but excluding any .zip files
  zip -r "$zip_name" . -x "*.zip"

  echo "File '$source_dir/$zip_name' created successfully."

  cd - > /dev/null || exit 1
}

zip_folder "$GERBER_DIR" "$GERBER_ZIP"
zip_folder "$PLACEMENT_DIR" "$PLACEMENT_ZIP"

echo "Done."
