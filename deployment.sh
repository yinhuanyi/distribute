#! /bin/bash

# 1：安装nfs
apt install -y nfs-kernel-server
systemctl restart  nfs-kernel-server
systemctl enable  nfs-kernel-server
PROJECT_DIR=`pwd`
sed -i "s#PROJECT_DIR#$PROJECT_DIR#g" $PROJECT_DIR/exports
cp -f $PROJECT_DIR/exports /etc/exports
exportfs -r

# 2：构建镜像
docker build -t fil-distribute:`date +%s` -f distribute.dockerfile .

# 3：获取镜像ID
LATEST_ID=`docker images | awk 'NR==2 && /fil-distribute/{printf "%s:%s\n",$1,$2}'`

# 4: 启动容器
docker run -d --name fil-distribute -v /app/fil-distribute:/app/fil-distribute -p 8007:8007 $LATEST_ID