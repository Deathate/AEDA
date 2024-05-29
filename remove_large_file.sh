find * -size +10M | while read -r file; do
    git rm  --cached  $file
done
