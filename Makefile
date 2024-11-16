WEB_CONTAINER_NAME = trend-backend

EXEC = docker exec -it $(WEB_CONTAINER_NAME)
MANAGEMENT_PREFIX = $(EXEC) python manage.py
DOCKER_COMPOSE = docker compose -f docker-compose.yml

build:
	# Build containers
	$(DOCKER_COMPOSE) build
run:
	# Run all containers
	$(DOCKER_COMPOSE) up
run-d:
	# Run all containers detached
	$(DOCKER_COMPOSE) up -d
stop:
	# Stop all currently running containers
	$(DOCKER_COMPOSE) stop
restart:
	# Restart docker container/s.
	docker container restart $(filter-out $@,$(MAKECMDGOALS))
down-and-clear:
	# Stop containers and remove containers, networks, volumes, and images.
	$(DOCKER_COMPOSE) down -v
clean-build: down-and-clear
	# Do a `down-and-clear` first and re-build containers.
	$(MAKE) build
clean-run: down-and-clear
	# Do a `down-and-clear` first and run containers.
	$(MAKE) run
clean-up-d: down-and-clear
	# Do a `down-and-clear` first and up containers detached.
	$(DOCKER_COMPOSE) up -d
clean-up-d-build: down-and-clear
	# Do a `down-and-clear` first then build and up containers detached.
	$(DOCKER_COMPOSE) up -d --build
migrations:
	# Make database migrations.
	$(MANAGEMENT_PREFIX) makemigrations
migrate:
	# Apply database migrations.
	$(MANAGEMENT_PREFIX) migrate
manage:
	# Run adhoc management commands
	$(MANAGEMENT_PREFIX) $(filter-out $@,$(MAKECMDGOALS))
shell:
	# Start a Django shell
	$(MANAGEMENT_PREFIX) shell
shell-plus:
	# Start a Django shell plus
	$(MANAGEMENT_PREFIX) shell_plus
bash:
	# Start a bash
	$(EXEC) bash
messages:
	# Build messages
	$(MANAGEMENT_PREFIX) makemessages --no-location --no-wrap -l ar
compilemessages:
	# Compile messages
	$(MANAGEMENT_PREFIX) compilemessages
test:
	# Run tests locally
	$(EXEC) pytest --durations=10 --durations-min=1.0 $(filter-out $@,$(MAKECMDGOALS))
ci-test:
	# Run pipeline tests
	$(EXEC) pytest -q --durations=10 --durations-min=1.0 --create-db $(filter-out $@,$(MAKECMDGOALS))
debug-test:
	# Run tests locally and enter PDB session when a test fails
	$(EXEC) pytest --pdb --durations=10 --durations-min=1.0 $(filter-out $@,$(MAKECMDGOALS))
coverage:
	# Generate HTML coverage report
	$(EXEC) coverage html
ci-test-image:
	# Build and push CI test image
	./scripts/make-ci-test-image.sh
