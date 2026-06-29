for img in scanned_pdfs/*.jpg; do
  echo "Processing $img"
  tesseract "$img" "${img%.jpg}"
done
