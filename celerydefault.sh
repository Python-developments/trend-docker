#!/bin/bash
echo "########################################"
echo "########################################"
echo "celerydefault.sh"
echo "########################################"
echo "########################################"
exec celery -A trend worker -l INFO --autoscale=2,1 --logfile=celery.log
