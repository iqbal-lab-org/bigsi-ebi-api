
Start minikube
```
minikube start
minikube mount /local/path/to/bigis_test_data/bigsi/:/data/bigsi/
```

In this example, the index file is called "test-bigsi-bdb" and will now be available via local filesystem at `/data/bigsi/test-bigsi-bdb` within the minikube VM. 

In order to make this available from within a k8 pod, we first need a volume and volume claim. 

```
## Volume mounts
kubectl create -f k8/bigsi-services/bigsi-1/pv-volume.yaml
kubectl create -f k8/bigsi-services/bigsi-1/pv-claim.yaml
```

Now, we can create the deployments and services

```
kubectl create -f k8/bigsi-services/bigsi-1/bigsi-deployment.yaml
```


## You can test these are working by running 
```
kubectl exec -it bigsi-1-deployment-f6c8c9c5-76nzt 
apt-get update -y && apt-get install curl -y
curl localhost/search?seq=CGGCGAGGAAGCGTTAAATCTCTTTCTGACG 
curl bigsi-1-service/search?seq=CGGCGAGGAAGCGTTAAATCTCTTTCTGACG 
```

BIGSI aggregator requires a redis instance to cache the results from a query and as a celery broker.

```
kubectl create -f k8/redis/redis-service.yaml
```

Build the image if required
```
eval $(minikube docker-env)
docker build -t phelimb/bigsi-aggregator. 
```

Then create the aggregator service

```
kubectl create -f k8/bigsi-aggregator-service/bigsi-aggregator-api-deployment.yaml
```

