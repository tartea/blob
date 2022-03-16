### 安装

```shell
brew install kafka
```

- kafka使用zookeeper管理，安装过程会自动安装zookeeper
- 安装目录：/usr/local/Cellar/kafka/*    (*为具体安装的版本)
- 配置文件目录：/usr/local/etc/kafka

### 修改配置文件

```shell
vi /usr/local/etc/kafka/server.properties
```

修改kafka的监听地址和端口为localhost:9092

```shell
listeners=PLAINTEXT://localhost:9092
```

### 启动服务

```shell
brew services start zookeeper
brew services start kafka
```

由于kafka依赖zookeeper管理，所以zookeeper需要先启动

### 可视化界面

[下载地址https://www.kafkatool.com/download.html](https://www.kafkatool.com/download.html)

![image-20220316210739473](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202203162107628.png)

配置完上面的信息，就可以连接使用了