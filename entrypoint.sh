echo "########################################"
echo "########################################"
echo "entrypoint.sh"
echo "########################################"
echo "########################################"
python manage.py makemigrations
python manage.py migrate
echo "########################################"
echo "########################################"