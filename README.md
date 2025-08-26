# Build and Push
docker buildx build \               
  --platform linux/amd64,linux/arm64 \
  --tag registry.sparkfly.cloud/library/pangolin-operator:0.1.0 \
  --tag registry.sparkfly.cloud/library/pangolin-operator:latest \
  --push \
  .

# Only Build
# amd64
docker buildx build \
  --platform linux/amd64 \
  -t registry.sparkfly.cloud/library/pangolin-operator:0.1.0-amd64 \
  -t registry.sparkfly.cloud/library/pangolin-operator:latest-amd64 \
  --load .

docker save registry.sparkfly.cloud/library/pangolin-operator:0.1.0-amd64 \
  -o pangolin-operator-0.1.0-amd64.tar

# arm64
docker buildx build \
  --platform linux/arm64 \
  -t registry.sparkfly.cloud/library/pangolin-operator:0.1.0-arm64 \
  -t registry.sparkfly.cloud/library/pangolin-operator:latest-arm64 \
  --load .

docker save registry.sparkfly.cloud/library/pangolin-operator:0.1.0-arm64 \
  -o pangolin-operator-0.1.0-arm64.tar


docker manifest create registry.sparkfly.cloud/library/pangolin-operator:0.1.0 \
  --amend registry.sparkfly.cloud/library/pangolin-operator:0.1.0-amd64 \
  --amend registry.sparkfly.cloud/library/pangolin-operator:0.1.0-arm64

docker manifest annotate registry.sparkfly.cloud/library/pangolin-operator:0.1.0 \
  registry.sparkfly.cloud/library/pangolin-operator:0.1.0-amd64 --arch amd64
docker manifest annotate registry.sparkfly.cloud/library/pangolin-operator:0.1.0 \
  registry.sparkfly.cloud/library/pangolin-operator:0.1.0-arm64 --arch arm64

docker manifest push registry.sparkfly.cloud/library/pangolin-operator:0.1.0