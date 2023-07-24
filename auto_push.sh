# chmod +x ./auto_push.sh to allow terminal to run script
touch ./docs/test.txt
git add .
git commit -m "auto git upload"
git push -u
