REGISTRY_HOST = 80.78.247.11:5000
IMAGE_NAME = fastapi-test-app
VERSION = 1.0.0

.PHONY: login build push bp

login:
	docker login $(REGISTRY_HOST) -u admin -p admin123

build:
	docker build -t $(REGISTRY_HOST)/$(IMAGE_NAME):$(VERSION) .
	docker tag $(REGISTRY_HOST)/$(IMAGE_NAME):$(VERSION) $(REGISTRY_HOST)/$(IMAGE_NAME):latest

push: login
	docker push $(REGISTRY_HOST)/$(IMAGE_NAME):$(VERSION)
	docker push $(REGISTRY_HOST)/$(IMAGE_NAME):latest

bp: build push