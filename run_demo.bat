@echo off
echo --- Starting Demo Setup for dj-editor-js ---

IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment. Make sure python and venv are installed and in your PATH.
        goto :eof
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

cd example

echo Installing requirements...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install requirements.
    goto :eof
)

echo Running database migrations...
python manage.py migrate

echo Creating migrations for the blog app...
python manage.py makemigrations blog
echo Running database migrations...
python manage.py migrate

echo Checking for superuser...
echo from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser "admin" created.') if not User.objects.filter(username='admin').exists() else print('Superuser "admin" already exists.'); User.objects.create_superuser('admin', 'admin@example.com', 'password') if not User.objects.filter(username='admin').exists() else None | python manage.py shell

echo.
echo --- Setup complete! ---
echo Starting the Django development server at http://127.0.0.1:8000
echo Login to the admin with:
echo Username: admin
echo Password: password
echo.
echo Press Ctrl+C to stop the server.
python manage.py runserver

