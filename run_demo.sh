#!/bin/bash

# Script to set up and run the Django demo project.

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}--- Starting Demo Setup for dj-editor-js ---${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Make sure python3 and venv are installed."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo -e "${YELLOW}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "Error: Failed to upgrade pip."
    exit 1
fi

cd example

echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements."
    exit 1
fi

echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate

echo -e "${YELLOW}Creating migrations for the blog app...${NC}"
python manage.py makemigrations blog

echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate

echo -e "${YELLOW}Checking for superuser...${NC}"
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'password')
    print('Superuser "admin" with password "password" created.')
else:
    print('Superuser "admin" already exists.')
EOF

echo -e "\n${GREEN}--- Setup complete! ---${NC}"
echo -e "Starting the Django development server at ${YELLOW}http://127.0.0.1:8000${NC}"
echo "Login to the admin with:"
echo "Username: admin"
echo "Password: password"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop the server."
python manage.py runserver

