pip freeze --exclude-editable | sed s/=.*// > requirements.txt