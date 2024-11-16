#!/bin/bash
echo "########################################"
echo "########################################"
echo "celery-beat-entrypoint.sh"
echo "########################################"
echo "########################################"
exec celery -A trend beat -l info --logfile=celery_beat.log
