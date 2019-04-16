export USER="nathantheinventor"
export OC_PROJECT_NAME="open-contest"
export OC_CODE_DIR=~/open-contest/src/main/
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/db/:/db \
    -v /tmp:/tmp \
    -v $OC_CODE_DIR/:/code \
    -v $OC_CODE_DIR/nginx.conf:/etc/nginx/sites-enabled/nginx.conf \
    -p 0.0.0.0:8000:8000/tcp \
    $USER/$OC_PROJECT_NAME
