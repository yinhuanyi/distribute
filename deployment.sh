#! /bin/bash

# 1：安装nfs
apt install -y nfs-kernel-server
systemctl restart  nfs-kernel-server
systemctl enable  nfs-kernel-server
PROJECT_DIR=`pwd`
sed -i "s#PROJECT_DIR#$PROJECT_DIR#g" $PROJECT_DIR/exports
cp -f $PROJECT_DIR/exports /etc/exports
exportfs -r

# 2：安装docker
DOCKER_ENGINE=`docker -v | grep Docker`
# 如果docker没有安装
if [ -z $DOCKER_ENGINE ]; then
    curl -sSL https://get.docker.com/ | sh
fi

# 3：构建镜像
docker build -t distribute:`date +%s` -f distribute.dockerfile .

# 4：获取镜像ID
LATEST_ID=`docker images | awk 'NR==2 && /distribute/{printf "%s:%s\n",$1,$2}'`

# 5: 启动容器
docker run -d --name distribute -v /app/distribute:/app/distribute -p 8007:8007 $LATEST_ID